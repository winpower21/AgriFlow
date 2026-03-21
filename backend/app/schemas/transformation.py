"""
Transformation Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

# ── Transformation Type ──────────────────────────────


class TransformationTypeBase(BaseModel):
    name: str
    is_root: Optional[bool] = None
    description: Optional[str] = None
    measures_personnel_efficiency: bool = True


class TransformationTypeCreate(TransformationTypeBase):
    pass


class TransformationTypeUpdate(BaseModel):
    name: Optional[str] = None
    is_root: Optional[bool] = None
    description: Optional[str] = None
    measures_personnel_efficiency: bool | None = None


class TransformationTypeSchema(TransformationTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ── Sub-resource Create/Update schemas ──────────────────────


class TransformationInputCreate(BaseModel):
    batch_id: int
    input_weight: Decimal


class TransformationOutputCreate(BaseModel):
    batch_code: str
    output_weight: Decimal
    stage_id: int
    notes: Optional[str] = None
    plantation_id: Optional[int] = None  # Used for root (harvest) transformations


class TransformationPersonnelCreate(BaseModel):
    personnel_id: int
    days_worked: Decimal  # Required for both wage types
    output_weight_considered: Optional[Decimal] = None  # Optional for DAILY, required for PER_KG
    additional_payments: Decimal = Decimal("0")
    additional_payments_description: Optional[str] = None
    notes: Optional[str] = None


class TransformationPersonnelUpdate(BaseModel):
    days_worked: Optional[Decimal] = None
    output_weight_considered: Optional[Decimal] = None
    additional_payments: Optional[Decimal] = None
    additional_payments_description: Optional[str] = None
    notes: Optional[str] = None


class TransformationVehicleCreate(BaseModel):
    vehicle_id: int
    hours_used: Decimal
    fuel_qty: Decimal
    notes: Optional[str] = None


class TransformationVehicleUpdate(BaseModel):
    hours_used: Optional[Decimal] = None
    fuel_qty: Optional[Decimal] = None
    notes: Optional[str] = None


class TransformationConsumableCreate(BaseModel):
    consumable_id: int
    quantity_used: Decimal
    consumption_date: datetime
    notes: Optional[str] = None


class TransformationExpenseCreate(BaseModel):
    category_id: int
    amount: Decimal
    description: Optional[str] = None
    date: datetime


# ── Enriched response sub-schemas ────────────────────


class TransformationInputDetail(BaseModel):
    id: int
    transformation_id: int
    batch_id: int
    batch_code: Optional[str] = None
    stage_name: Optional[str] = None
    input_weight: Decimal
    model_config = ConfigDict(from_attributes=True)


class TransformationOutputDetail(BaseModel):
    id: int
    transformation_id: int
    batch_id: int
    batch_code: Optional[str] = None
    stage_name: Optional[str] = None
    output_weight: Decimal
    model_config = ConfigDict(from_attributes=True)


class PersonnelAssignmentDetail(BaseModel):
    id: int
    transformation_id: int
    personnel_id: int
    personnel_name: Optional[str] = None
    assignment_date: datetime
    wage_type_at_time_id: int
    wage_type_name: Optional[str] = None
    rate_at_time: Decimal
    days_worked: Optional[Decimal] = None
    output_weight_considered: Optional[Decimal] = None
    additional_payments: Decimal
    additional_payments_description: Optional[str] = None
    base_wage: Optional[Decimal] = None
    total_wages_payable: Optional[Decimal] = None
    is_paid: bool = False
    expense_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VehicleUsageDetail(BaseModel):
    id: int
    transformation_id: int
    vehicle_id: int
    vehicle_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    fuel_consumable_name: Optional[str] = None
    hours_used: Decimal
    fuel_qty: Decimal
    fuel_cost: Optional[Decimal] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ConsumableUsageDetail(BaseModel):
    id: int
    transformation_id: int
    consumable_id: int
    consumable_name: Optional[str] = None
    consumable_unit: Optional[str] = None
    consumption_date: datetime
    quantity_used: Decimal
    total_cost: Decimal
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TransformationExpenseDetail(BaseModel):
    id: int
    date: datetime
    amount: Decimal
    category_id: int
    category_name: Optional[str] = None
    description: Optional[str] = None
    transformation_id: Optional[int] = None
    is_wage_expense: bool = False  # True if linked via TransformationPersonnel
    model_config = ConfigDict(from_attributes=True)


# ── Transformation ──────────────────────────────


class TransformationCreate(BaseModel):
    """POST /transformations — only type_id, from_date, notes. to_date starts null."""

    type_id: int
    from_date: datetime
    notes: Optional[str] = None


class TransformationUpdate(BaseModel):
    """PUT /transformations/{id} — notes, from_date, to_date only (no type_id)."""

    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    notes: Optional[str] = None


class TransformationSchema(BaseModel):
    id: int
    type_id: int
    # is_root: Optional[bool] = None
    from_date: datetime
    to_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    transformation_type: TransformationTypeSchema
    inputs: List[TransformationInputDetail] = []
    outputs: List[TransformationOutputDetail] = []
    personnel_assignments: List[PersonnelAssignmentDetail] = []
    vehicle_usage: List[VehicleUsageDetail] = []
    consumable_consumptions: List[ConsumableUsageDetail] = []
    expenses: List[TransformationExpenseDetail] = []
    remaining_assignable_output_qty: Optional[Decimal] = None
    model_config = ConfigDict(from_attributes=True)


class TransformationListItem(BaseModel):
    """Lightweight schema for list views."""

    id: int
    type_id: int
    type_name: Optional[str] = None
    from_date: datetime
    to_date: Optional[datetime] = None
    notes: Optional[str] = None
    is_complete: bool
    input_batch_codes: List[str] = []
    total_input_weight: Optional[Decimal] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
