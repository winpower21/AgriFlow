from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class VehicleCreate(BaseModel):
    number: str
    vehicle_type: Optional[str] = None


class VehicleUpdate(BaseModel):
    number: Optional[str] = None
    vehicle_type: Optional[str] = None
    is_active: Optional[bool] = None


class VehicleSchema(BaseModel):
    id: int
    number: str
    vehicle_type: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
