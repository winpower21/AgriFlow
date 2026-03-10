from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ConsumableCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ConsumableCategorySchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsumableCreate(BaseModel):
    name: str
    unit: str
    description: Optional[str] = None
    category_id: Optional[int] = None


class ConsumableUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None


class ConsumableSchema(BaseModel):
    id: int
    name: str
    unit: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    category_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ConsumablePurchaseCreate(BaseModel):
    purchase_date: datetime
    quantity: Decimal
    unit_cost: Decimal
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None


class ConsumablePurchaseSchema(BaseModel):
    id: int
    consumable_id: int
    purchase_date: datetime
    quantity: Decimal
    unit_cost: Decimal
    remaining_quantity: Decimal
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None
    expense_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsumableWithStockSchema(ConsumableSchema):
    """Consumable with computed stock totals."""
    total_purchased: Decimal = Decimal("0")
    total_remaining: Decimal = Decimal("0")
