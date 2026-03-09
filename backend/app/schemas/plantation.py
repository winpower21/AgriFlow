"""
Plantation and lease Pydantic schemas.

Key changes from v1:
  - PlantationCreate/Update now accept ``location_id`` (int FK) instead of
    a nested LocationSchema.  Location creation/lookup is handled separately
    by the ``GET /locations/search`` and ``POST /locations/resolve`` endpoints.
  - ``area_hectares`` and ``lease_cost`` added to create/update schemas.
  - ``PlantationSchema`` exposes ``is_active`` (computed Python property on
    the ORM model) and ``area_hectares``.
  - ``LeaseAddRequest`` supports adding a lease from the detail modal without
    going through the full plantation update flow.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from .batch import BatchSchema
from .location import LocationSchema


# ── Lease schemas ──────────────────────────────────────────────────────────────

class LeaseCreate(BaseModel):
    """Request body for creating a new lease tied to a plantation."""

    plantation_id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    cost: Optional[Decimal] = None


class LeaseAddRequest(BaseModel):
    """Request body for appending a lease from the detail modal.

    Does not require ``plantation_id`` — taken from the URL parameter.
    """

    start_date: datetime
    end_date: Optional[datetime] = None
    cost: Optional[Decimal] = None


class LeaseSchema(BaseModel):
    """API response schema for a plantation lease record."""

    id: int
    plantation_id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    cost: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


# ── Plantation schemas ─────────────────────────────────────────────────────────

class PlantationCreate(BaseModel):
    """Request body for creating a new plantation.

    Location is supplied as a pre-existing ``location_id`` (resolved via
    ``GET /locations/search`` or ``POST /locations/resolve`` before this call).
    An initial lease period may be included in the same request.
    """

    name: str
    location_id: Optional[int] = None
    area_hectares: Optional[Decimal] = None
    lease_start: Optional[datetime] = None
    lease_end: Optional[datetime] = None
    lease_cost: Optional[Decimal] = None


class PlantationUpdate(BaseModel):
    """Request body for partially updating a plantation (PATCH-style).

    All fields are optional; only supplied fields are applied.
    Providing ``lease_start`` appends a new lease record (does not overwrite).
    """

    name: Optional[str] = None
    location_id: Optional[int] = None
    area_hectares: Optional[Decimal] = None
    lease_start: Optional[datetime] = None
    lease_end: Optional[datetime] = None
    lease_cost: Optional[Decimal] = None


class PlantationSchema(BaseModel):
    """Full API response schema for a plantation record."""

    id: int
    name: str
    location_id: Optional[int] = None
    area_hectares: Optional[Decimal] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    location: Optional[LocationSchema] = None
    lease: List[LeaseSchema] = []
    batches: Optional[List[BatchSchema]] = None

    model_config = ConfigDict(from_attributes=True)


class DeleteCheckResponse(BaseModel):
    """Response for the plantation delete-check endpoint."""

    has_history: bool
    history_count: int
