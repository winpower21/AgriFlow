import json
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, field_validator


class ApprovalItem(BaseModel):
    """One item inside a batch approval request."""
    index: int
    status: str = "pending"          # pending | approved | rejected
    data: Dict[str, Any]             # original submitted data
    modified_data: Optional[Dict[str, Any]] = None   # admin overrides
    rejection_note: Optional[str] = None


class ApprovalRequestCreate(BaseModel):
    type: Literal["EXPENSE", "CONSUMABLE_PURCHASE", "TRANSFORMATION_COMPLETION", "PERSONNEL_PAYMENT", "TRANSFORMATION_EXPENSE"]
    items: List[ApprovalItem]
    notes: Optional[str] = None


class ApprovalRequestUpdate(BaseModel):
    items: List[ApprovalItem]
    notes: Optional[str] = None


class ApprovalItemAction(BaseModel):
    action: Literal["approve", "approve_with_edits", "reject"]
    modified_data: Optional[Dict[str, Any]] = None
    rejection_note: Optional[str] = None


class ApprovalRequestorSchema(BaseModel):
    id: int
    email: str
    model_config = ConfigDict(from_attributes=True)


class ApprovalRequestSchema(BaseModel):
    id: int
    type: str
    status: str
    requested_by_id: int
    requested_by: ApprovalRequestorSchema
    payload: List[ApprovalItem]       # deserialized
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    @field_validator("payload", mode="before")
    @classmethod
    def parse_payload(cls, v):
        if isinstance(v, str):
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else parsed.get("items", parsed)
        return v

    model_config = ConfigDict(from_attributes=True)
