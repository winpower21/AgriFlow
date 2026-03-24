import decimal
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
            payload=json.dumps(items, default=lambda o: str(o) if isinstance(o, decimal.Decimal) else None),
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

        req.payload = json.dumps(items, default=lambda o: str(o) if isinstance(o, decimal.Decimal) else None)
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
        req.payload = json.dumps(items, default=lambda o: str(o) if isinstance(o, decimal.Decimal) else None)
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
        req.payload = json.dumps(items, default=lambda o: str(o) if isinstance(o, decimal.Decimal) else None)
        req.reviewed_by_id = admin_id
        req.reviewed_at = datetime.utcnow()
        req.status = "RESOLVED"
        self.db.commit()
        return self._q().filter(ApprovalRequest.id == request_id).first()

    def update(self, request_id: int, user_id: int, data) -> Optional[ApprovalRequest]:
        """Manager edits their own pending request."""
        req = self.db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
        if not req:
            return None
        if req.requested_by_id != user_id:
            raise ValueError("not_owner")
        if req.status != "PENDING":
            raise ValueError("not_pending")

        items = [item.model_dump() for item in data.items]
        for i, item in enumerate(items):
            item["index"] = i
            item["status"] = "pending"
        req.payload = json.dumps(items, default=lambda o: str(o) if isinstance(o, decimal.Decimal) else None)
        if data.notes is not None:
            req.notes = data.notes
        self.db.commit()
        return self._q().filter(ApprovalRequest.id == request_id).first()

    def delete(self, request_id: int, user_id: int) -> Optional[str]:
        """Manager deletes their own pending request. Returns error string or None."""
        req = self.db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
        if not req:
            return "not_found"
        if req.requested_by_id != user_id:
            return "not_owner"
        if req.status != "PENDING":
            return "not_pending"
        self.db.delete(req)
        self.db.commit()
        return None

    def _compute_status(self, items: list) -> str:
        statuses = {i["status"] for i in items}
        if "pending" not in statuses:
            return "RESOLVED"
        if len(statuses) > 1:
            return "PARTIAL"
        return "PENDING"

    def _execute_approved_item(self, req_type: str, data: dict):
        if req_type == "EXPENSE":
            expense_data = ExpenseCreate(**data)
            ExpenseService(self.db).create(expense_data)
        elif req_type == "CONSUMABLE_PURCHASE":
            data = dict(data)
            consumable_id = data.pop("consumable_id")
            purchase_data = ConsumablePurchaseCreate(**data)
            ConsumableService(self.db).add_purchase(consumable_id, purchase_data)
        elif req_type == "TRANSFORMATION_COMPLETION":
            self._execute_transformation_completion(data)
        elif req_type == "PERSONNEL_PAYMENT":
            self._execute_personnel_payment(data)
        elif req_type == "TRANSFORMATION_EXPENSE":
            self._execute_transformation_expense(data)

    def _execute_transformation_completion(self, data: dict):
        from ..crud.transformation import TransformationService
        from datetime import datetime, timezone

        t_id = data["transformation_id"]
        completion_date_str = data.get("completion_date")
        completion_date = None
        if completion_date_str:
            completion_date = datetime.fromisoformat(completion_date_str)
            if completion_date.tzinfo is None:
                completion_date = completion_date.replace(tzinfo=timezone.utc)

        svc = TransformationService(self.db)
        # Guard: skip if already complete
        t = svc.get_by_id(t_id)
        if t and t.to_date is not None:
            return  # Already complete, skip
        result = svc.complete(t_id, completion_date=completion_date)
        if result is not None:
            raise ValueError(f"Failed to complete transformation {t_id}: {result}")

    def _execute_personnel_payment(self, data: dict):
        from ..crud.transformation import TransformationService
        from ..models.personnel import TransformationPersonnel
        from decimal import Decimal

        t_id = data["transformation_id"]
        tp_id = data["personnel_assignment_id"]

        # Apply additional_payments override if present in approved data
        if data.get("additional_payments") is not None:
            tp = self.db.query(TransformationPersonnel).filter(
                TransformationPersonnel.id == tp_id,
                TransformationPersonnel.transformation_id == t_id,
            ).first()
            if tp:
                tp.additional_payments = Decimal(str(data["additional_payments"]))
                if "additional_payments_description" in data and data["additional_payments_description"] is not None:
                    tp.additional_payments_description = data["additional_payments_description"]
                self.db.flush()

        svc = TransformationService(self.db)
        result = svc.mark_personnel_paid(t_id, tp_id)
        if result in ("already_paid", "not_found"):
            return  # Guard: skip if already paid or assignment was deleted
        if result is not None:
            raise ValueError(f"Failed to mark personnel paid: {result}")

    def _execute_transformation_expense(self, data: dict):
        from datetime import datetime, timezone

        expense_data = ExpenseCreate(
            date=data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            amount=data["amount"],
            category_id=data["category_id"],
            description=data.get("description", ""),
            transformation_id=data["transformation_id"],
        )
        ExpenseService(self.db).create(expense_data)
