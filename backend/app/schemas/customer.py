from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CustomerCreate(BaseModel):
    name: str
    phone: str
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerSchema(BaseModel):
    id: int
    name: str
    phone: str
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
