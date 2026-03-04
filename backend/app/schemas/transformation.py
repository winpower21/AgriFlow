from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

# ── Transformation Type ──────────────────────────────


class TransformationTypeBase(BaseModel):
    name: str
    description: Optional[str] = None


class TransformationTypeCreate(TransformationTypeBase):
    pass


class TransformationTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TransformationTypeSchema(TransformationTypeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ── Transformation ──────────────────────────────


class TransformationBase(BaseModel):
    type_id: int
    from_date: datetime
    to_date: datetime
    notes: str | None = None


class TransformationCreate(TransformationBase):
    pass


class TransformationUpdate(TransformationBase):
    id: int
    pass


class TransformationInput(BaseModel):
    transformation_id: int
    batch_id: int
    input_weight: Decimal

    model_config = ConfigDict(from_attributes=True)


class TransformationOutput(BaseModel):
    transformation_id: int
    batch_id: int
    output_weight: Decimal

    model_config = ConfigDict(from_attributes=True)


class TransformationSchema(TransformationBase):
    id: int
    inputs: List[TransformationInput]
    outputs: List[TransformationOutput]
    personnel_assignments: List[PersonnelAssignment]
    created_at: datetime
    updated_at: datetime
    vehicle_usage: List[VehicleUsage]
    consumable_consumptions: List[ConsumableConsumption]
    transformation_type: TransformationType
