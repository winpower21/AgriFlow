"""
Personnel (worker) Pydantic schemas.

Defines the request and response models for managing agricultural workers,
including their wage type and current pay rate.  The ``WageTypeSchema`` here
is a lightweight read-only reference used when nesting wage type info inside
a personnel response.
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WageTypeSchema(BaseModel):
    """Lightweight read-only schema for wage type data embedded in personnel responses.

    Fields:
        id:   Primary key of the wage type.
        name: Label of the wage type (e.g. 'Daily', 'Piece-rate', 'Monthly').
    """

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class PersonnelBase(BaseModel):
    """Base personnel schema with shared fields used by create and read models.

    Fields:
        name:          Full name of the worker.
        wage_type_id:  FK to the wage type that determines how this worker is paid.
        current_rate:  The worker's current wage rate (per day, per kg, etc.,
                       depending on the wage type).
        phone:         Optional contact phone number.
        address:       Optional home address.
    """

    name: str
    wage_type_id: int
    current_rate: Decimal
    phone: Optional[str] = None
    address: Optional[str] = None


class PersonnelCreate(PersonnelBase):
    """Request body for registering a new worker.

    Inherits all fields from PersonnelBase. The ``id``, ``is_active``, and
    timestamps are generated server-side.
    """

    pass


class PersonnelUpdate(BaseModel):
    """Request body for updating an existing worker's details (PATCH-style).

    All fields are optional; only supplied fields are modified.
    Setting ``is_active`` to False effectively soft-deletes the worker.
    """

    name: Optional[str] = None
    wage_type_id: Optional[int] = None
    current_rate: Optional[Decimal] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class PersonnelSchema(PersonnelBase):
    """API response schema for a personnel (worker) record.

    Extends PersonnelBase with server-managed fields and the nested
    ``wage_type`` object so the client can display the wage type label
    without a separate lookup.
    """

    id: int
    photo: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Nested wage type details for display convenience.
    wage_type: WageTypeSchema

    model_config = ConfigDict(from_attributes=True)
