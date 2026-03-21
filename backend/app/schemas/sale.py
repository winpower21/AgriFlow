from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, model_validator

PaymentMethodType = Literal["CASH", "BANK_TRANSFER", "UPI"]


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
    is_paid: bool = False
    payment_method: Optional[PaymentMethodType] = None

    @model_validator(mode='after')
    def validate_payment(self):
        if self.is_paid and not self.payment_method:
            raise ValueError('payment_method is required when is_paid is True')
        return self


class SaleReject(BaseModel):
    rejection_reason: Optional[str] = None


class SaleMarkPaid(BaseModel):
    payment_method: PaymentMethodType


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
    invoice_number: Optional[str] = None
    is_paid: bool = False
    payment_method: Optional[str] = None

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

    is_paid: bool = False
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None
    paid_by_name: Optional[str] = None

    allocations: list[SaleAllocationSchema] = []

    model_config = ConfigDict(from_attributes=True)


class SalesKPIs(BaseModel):
    total_sales_count: int
    total_revenue: Decimal
    total_volume_kg: Decimal
    avg_sale_value: Decimal
    outstanding_credit_amount: Decimal
    paid_amount: Decimal
    total_profit: Optional[Decimal] = None
    avg_profit_margin: Optional[Decimal] = None
    paid_count: int
    credit_count: int


class TimePeriodMetric(BaseModel):
    period: str
    revenue: Decimal
    volume_kg: Decimal
    count: int


class StageMetric(BaseModel):
    stage_name: str
    revenue: Decimal
    volume_kg: Decimal
    count: int


class CustomerMetric(BaseModel):
    customer_id: int
    customer_name: str
    revenue: Decimal
    volume_kg: Decimal


class PaymentBreakdown(BaseModel):
    paid_count: int
    paid_amount: Decimal
    credit_count: int
    credit_amount: Decimal


class ProfitTimePeriodMetric(BaseModel):
    period: str
    profit: Decimal
    margin_pct: Decimal


class SalesAnalyticsResponse(BaseModel):
    granularity: str
    kpis: SalesKPIs
    revenue_over_time: list[TimePeriodMetric]
    volume_over_time: list[TimePeriodMetric]
    sales_by_stage: list[StageMetric]
    top_customers: list[CustomerMetric]
    payment_breakdown: PaymentBreakdown
    profit_over_time: list[ProfitTimePeriodMetric]
