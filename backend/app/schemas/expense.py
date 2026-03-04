from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .settings import ExpenseCategorySchema


class ExpenseCreate(BaseModel):
    date: datetime
    amount: Decimal
    category_id: int
    plantation_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    description: Optional[str] = None


class ExpenseSchema(BaseModel):
    id: int
    date: datetime
    amount: Decimal
    category_id: int
    plantation_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    category: ExpenseCategorySchema

    model_config = ConfigDict(from_attributes=True)
