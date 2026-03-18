from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ManualAllocationItem(BaseModel):
    batch_id: int


class SaleCreate(BaseModel):
    customer_id: int
    stage_id: int
    sale_date: datetime
    quantity_sold: Decimal
    selling_price: Decimal
    allocation_mode: str  # "FIFO" or "MANUAL"
    manual_allocations: Optional[list[ManualAllocationItem]] = None
    notes: Optional[str] = None


class SaleReject(BaseModel):
    rejection_reason: Optional[str] = None


class SaleAllocationSchema(BaseModel):
    id: int
    sale_id: int
    batch_id: int
    quantity_allocated: Decimal
    cost_allocated: Decimal
    batch_code: Optional[str] = None
    batch_cost_per_kg: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class SaleListItem(BaseModel):
    id: int
    sale_date: datetime
    customer_name: str
    customer_phone: str
    stage_name: str
    quantity_sold: Decimal
    selling_price: Decimal
    cost_of_goods_sold: Decimal
    profit: Decimal
    profit_margin: Decimal
    status: str
    allocation_mode: str

    model_config = ConfigDict(from_attributes=True)


class SaleDetail(BaseModel):
    id: int
    sale_date: datetime
    quantity_sold: Decimal
    selling_price: Decimal
    cost_of_goods_sold: Decimal
    profit: Decimal
    profit_margin: Decimal
    unit_selling_price: Decimal
    status: str
    allocation_mode: str
    invoice_number: Optional[str] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime] = None

    customer_id: int
    customer_name: str
    customer_phone: str
    customer_address: Optional[str] = None
    customer_notes: Optional[str] = None

    stage_id: int
    stage_name: str

    created_by_name: Optional[str] = None
    reviewed_by_name: Optional[str] = None

    allocations: list[SaleAllocationSchema] = []

    model_config = ConfigDict(from_attributes=True)
