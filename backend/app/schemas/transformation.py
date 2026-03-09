"""
Transformation Pydantic schemas.

A *transformation* represents a processing step that converts one or more
input batches into one or more output batches (e.g. HARVEST -> CLEAN,
CLEAN -> DRY).  Each transformation can track:

- **Inputs / Outputs** -- the batches and weights consumed / produced.
- **Personnel assignments** -- workers assigned to the transformation with
  frozen wage rates (historical cost freezing).
- **Vehicle usage** -- machinery hours and fuel with frozen cost-per-hour.
- **Consumable consumption** -- materials consumed (bags, chemicals, etc.)
  with frozen costs.

Transformation *types* are a configurable lookup table (e.g. "Cleaning",
"Drying", "Grading").
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

# ── Transformation Type ──────────────────────────────


class TransformationTypeBase(BaseModel):
    """Base schema for transformation types (configurable lookup).

    Fields:
        name:        Short label for the type (e.g. 'Cleaning', 'Drying').
        description: Optional longer explanation of what this type entails.
    """
    name: str
    description: Optional[str] = None


class TransformationTypeCreate(TransformationTypeBase):
    """Request body for creating a new transformation type.

    Inherits all fields from TransformationTypeBase.
    """
    pass


class TransformationTypeUpdate(BaseModel):
    """Request body for updating an existing transformation type (PATCH-style).

    All fields are optional; only supplied fields are modified.
    """
    name: Optional[str] = None
    description: Optional[str] = None


class TransformationTypeSchema(TransformationTypeBase):
    """API response schema for a transformation type record.

    Adds the server-generated ``id`` primary key.
    """
    id: int

    model_config = ConfigDict(from_attributes=True)


# ── Transformation Inputs / Outputs ──────────────────


class TransformationInputSchema(BaseModel):
    """API response schema for a transformation input (batch consumed).

    Fields:
        transformation_id: FK to the parent transformation.
        batch_id:          FK to the batch that material was drawn from.
        input_weight:      Weight (kg) consumed from the source batch.
    """
    id: int
    transformation_id: int
    batch_id: int
    input_weight: Decimal

    model_config = ConfigDict(from_attributes=True)


class TransformationOutputSchema(BaseModel):
    """API response schema for a transformation output (batch produced).

    Fields:
        transformation_id: FK to the parent transformation.
        batch_id:          FK to the newly created output batch.
        output_weight:     Weight (kg) produced into the new batch.
    """
    id: int
    transformation_id: int
    batch_id: int
    output_weight: Decimal

    model_config = ConfigDict(from_attributes=True)


# ── Personnel Assignment ─────────────────────────────


class PersonnelAssignmentSchema(BaseModel):
    """API response schema for a personnel assignment within a transformation.

    Records which worker was assigned, and freezes their wage details at the
    time of assignment to support historical cost tracking.

    Fields:
        personnel_id:               FK to the assigned worker.
        assignment_date:            Date the worker was assigned.
        wage_type_at_time_id:       FK to the wage type in effect at assignment time.
        rate_at_time:               Frozen wage rate at the moment of assignment.
        days_worked:                Number of days the worker contributed (for daily wages).
        output_weight_considered:   Weight attributed to this worker (for piece-rate wages).
        additional_payments:        Any bonus or extra payments made.
        additional_payments_description: Free-text description of additional payments.
        wage_paid:                  Total wage disbursed for this assignment.
        notes:                      Optional free-text notes.
    """
    id: int
    transformation_id: int
    personnel_id: int
    assignment_date: datetime
    wage_type_at_time_id: int
    rate_at_time: Decimal
    days_worked: Optional[Decimal] = None
    output_weight_considered: Optional[Decimal] = None
    additional_payments: Decimal
    additional_payments_description: Optional[str] = None
    wage_paid: Decimal
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Vehicle Usage ────────────────────────────────────


class VehicleUsageSchema(BaseModel):
    """API response schema for vehicle / machinery usage in a transformation.

    Freezes the ``cost_per_hour`` at the time of recording for historical
    cost accuracy.

    Fields:
        vehicle_id:    FK to the vehicle / machinery used.
        hours_used:    Number of hours the vehicle was operated.
        fuel_consumed: Litres (or applicable unit) of fuel consumed.
        cost_per_hour: Frozen hourly rate at recording time.
        total_cost:    Pre-computed total (hours_used * cost_per_hour + fuel).
        notes:         Optional free-text notes.
    """
    id: int
    transformation_id: int
    vehicle_id: int
    hours_used: Decimal
    fuel_consumed: Decimal
    cost_per_hour: Decimal
    total_cost: Decimal
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Consumable Consumption ───────────────────────────


class ConsumableConsumptionSchema(BaseModel):
    """API response schema for consumable material usage in a transformation.

    Tracks items like bags, chemicals, or other supplies consumed during
    the processing step.

    Fields:
        consumable_id:    FK to the consumable item.
        consumption_date: Date the consumable was used.
        quantity_used:    Amount of the consumable consumed.
        total_cost:       Pre-computed monetary cost for the quantity used.
        notes:            Optional free-text notes.
    """
    id: int
    transformation_id: int
    consumable_id: int
    consumption_date: datetime
    quantity_used: Decimal
    total_cost: Decimal
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Transformation ──────────────────────────────


class TransformationBase(BaseModel):
    """Base transformation schema with shared fields.

    Fields:
        type_id:   FK to the TransformationType lookup.
        from_date: Start date of the transformation activity.
        to_date:   End date of the transformation activity.
        notes:     Optional free-text notes about the transformation.
    """
    type_id: int
    from_date: datetime
    to_date: datetime
    notes: str | None = None


class TransformationCreate(TransformationBase):
    """Request body for creating a new transformation.

    Inherits all fields from TransformationBase. Related inputs, outputs,
    personnel, vehicles, and consumables are typically added via separate
    endpoints after the transformation is created.
    """
    pass


class TransformationUpdate(BaseModel):
    """Request body for updating an existing transformation (PATCH-style).

    All fields are optional; only supplied fields are modified.
    """
    type_id: Optional[int] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    notes: Optional[str] = None


class TransformationSchema(TransformationBase):
    """Full API response schema for a transformation record.

    Nests all related sub-entities (type, inputs, outputs, personnel
    assignments, vehicle usage, consumable consumption) so the frontend
    can display a complete transformation detail view in one request.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    # Nested transformation type details.
    transformation_type: TransformationTypeSchema
    # Batches consumed by this transformation.
    inputs: List[TransformationInputSchema] = []
    # Batches produced by this transformation.
    outputs: List[TransformationOutputSchema] = []
    # Workers assigned with frozen wage snapshots.
    personnel_assignments: List[PersonnelAssignmentSchema] = []
    # Machinery usage with frozen cost snapshots.
    vehicle_usage: List[VehicleUsageSchema] = []
    # Consumable materials used during the transformation.
    consumable_consumptions: List[ConsumableConsumptionSchema] = []

    model_config = ConfigDict(from_attributes=True)
