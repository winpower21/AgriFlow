import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from ..models.approval import ApprovalRequest
from ..schemas.approval import ApprovalItem, ApprovalItemAction, ApprovalRequestCreate
from ..crud.expense import ExpenseService
from ..crud.consumable import ConsumableService
from ..schemas.expense import ExpenseCreate
from ..schemas.consumable import ConsumablePurchaseCreate


class ApprovalService:
    def __init__(self, db: Session):
        self.db = db

    def _q(self):
        return self.db.query(ApprovalRequest).options(
            joinedload(ApprovalRequest.requested_by),
        )

    def get_all(self, user_id: int, is_admin: bool) -> List[ApprovalRequest]:
        q = self._q()
        if not is_admin:
            q = q.filter(ApprovalRequest.requested_by_id == user_id)
        return q.order_by(ApprovalRequest.created_at.desc()).all()

    def get_by_id(self, request_id: int) -> Optional[ApprovalRequest]:
        return self._q().filter(ApprovalRequest.id == request_id).first()

    def create(self, user_id: int, data: ApprovalRequestCreate) -> ApprovalRequest:
        items = [item.model_dump() for item in data.items]
        for i, item in enumerate(items):
            item["index"] = i
            item["status"] = "pending"
        obj = ApprovalRequest(
            type=data.type,
            status="PENDING",
            requested_by_id=user_id,
            payload=json.dumps(items),
            notes=data.notes,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return self._q().filter(ApprovalRequest.id == obj.id).first()

    def act_on_item(
        self,
        request_id: int,
        item_index: int,
        action_data: ApprovalItemAction,
        admin_id: int,
    ) -> Optional[ApprovalRequest]:
        req = self.db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
        if not req:
            return None

        items: list = json.loads(req.payload)
        if item_index >= len(items):
            return None

        item = items[item_index]
        effective_data = action_data.modified_data or item["data"]

        if action_data.action in ("approve", "approve_with_edits"):
            item["status"] = "approved"
            item["modified_data"] = action_data.modified_data
            self._execute_approved_item(req.type, effective_data)
        elif action_data.action == "reject":
            item["status"] = "rejected"
            item["rejection_note"] = action_data.rejection_note

        req.payload = json.dumps(items)
        req.reviewed_by_id = admin_id
        req.reviewed_at = datetime.utcnow()
        req.status = self._compute_status(items)
        self.db.commit()
        return self._q().filter(ApprovalRequest.id == request_id).first()

    def approve_all(self, request_id: int, admin_id: int) -> Optional[ApprovalRequest]:
        req = self.db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
        if not req:
            return None
        items: list = json.loads(req.payload)
        for item in items:
            if item["status"] == "pending":
                item["status"] = "approved"
                self._execute_approved_item(req.type, item["data"])
        req.payload = json.dumps(items)
        req.reviewed_by_id = admin_id
        req.reviewed_at = datetime.utcnow()
        req.status = "RESOLVED"
        self.db.commit()
        return self._q().filter(ApprovalRequest.id == request_id).first()

    def reject_all(self, request_id: int, admin_id: int, note: Optional[str] = None) -> Optional[ApprovalRequest]:
        req = self.db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
        if not req:
            return None
        items: list = json.loads(req.payload)
        for item in items:
            if item["status"] == "pending":
                item["status"] = "rejected"
                if note:
                    item["rejection_note"] = note
        req.payload = json.dumps(items)
        req.reviewed_by_id = admin_id
        req.reviewed_at = datetime.utcnow()
        req.status = "RESOLVED"
        self.db.commit()
        return self._q().filter(ApprovalRequest.id == request_id).first()

    def _compute_status(self, items: list) -> str:
        statuses = {i["status"] for i in items}
        if "pending" not in statuses:
            return "RESOLVED"
        if len(statuses) > 1:
            return "PARTIAL"
        return "PENDING"

    def _execute_approved_item(self, req_type: str, data: dict):
        if req_type == "EXPENSE":
            # data dict keys must match ExpenseCreate fields
            expense_data = ExpenseCreate(**data)
            ExpenseService(self.db).create(expense_data)
        elif req_type == "CONSUMABLE_PURCHASE":
            # data must have consumable_id plus ConsumablePurchaseCreate fields
            data = dict(data)  # make a copy
            consumable_id = data.pop("consumable_id")
            purchase_data = ConsumablePurchaseCreate(**data)
            ConsumableService(self.db).add_purchase(consumable_id, purchase_data)
