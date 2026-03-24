"""
Expense Pydantic schemas.

Defines request and response models for recording miscellaneous operational
expenses.  Expenses are categorised (via ``ExpenseCategorySchema``) and can
optionally be linked to a specific plantation or vehicle for cost attribution.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .settings import ExpenseCategorySchema


class ExpenseCreate(BaseModel):
    """Request body for recording a new expense.

    Fields:
        date:           Date the expense was incurred.
        amount:         Monetary value of the expense.
        category_id:    FK to the expense category (e.g. 'Fuel', 'Supplies').
        plantation_id:  Optional FK to a plantation for site-level cost tracking.
        vehicle_id:     Optional FK to a vehicle if the expense is vehicle-related.
        description:    Optional free-text description of the expense.
    """
    date: datetime
    amount: Decimal
    category_id: int
    plantation_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    transformation_id: Optional[int] = None
    description: Optional[str] = None


class ExpenseUpdate(BaseModel):
    date: Optional[datetime] = None
    amount: Optional[Decimal] = None
    category_id: Optional[int] = None
    plantation_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    transformation_id: Optional[int] = None
    description: Optional[str] = None


class ExpenseSchema(BaseModel):
    """API response schema for an expense record.

    Mirrors ExpenseCreate but adds the server-generated ``id``, timestamps,
    and the nested ``category`` object so the frontend can display the
    category name without a separate lookup.
    """
    id: int
    date: datetime
    amount: Decimal
    category_id: int
    plantation_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    transformation_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Nested expense category for display convenience.
    category: ExpenseCategorySchema

    model_config = ConfigDict(from_attributes=True)
