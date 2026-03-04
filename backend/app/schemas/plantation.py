from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from .batch import BatchSchema
from .location import LocationSchema

# ── Plantation Lease ────────────────────────────────────


class LeaseCreate(BaseModel):
    plantation_id: int
    start_date: datetime
    end_date: datetime
    cost: Optional[Decimal] = None


class LeaseSchema(BaseModel):
    id: int
    plantation_id: int
    start_date: datetime
    end_date: datetime
    cost: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


# ── Plantation ───────────────────────────────────────


class PlantationBase(BaseModel):
    name: str
    location: Optional[LocationSchema] = None
    lease: Optional[LeaseSchema] = None


class PlantationCreate(PlantationBase):
    pass


class PlantationUpdate(PlantationBase):
    pass


class PlantationSchema(PlantationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    batches: Optional[List[BatchSchema]] = None
    model_config = ConfigDict(from_attributes=True)


class DeleteCheckResponse(BaseModel):
    has_history: bool
    history_count: int
