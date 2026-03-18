from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, model_validator


class VehicleCreate(BaseModel):
    number: str
    vehicle_type: Optional[str] = None
    fuel_consumable_id: Optional[int] = None


class VehicleUpdate(BaseModel):
    number: Optional[str] = None
    vehicle_type: Optional[str] = None
    is_active: Optional[bool] = None
    fuel_consumable_id: Optional[int] = None


class VehicleSchema(BaseModel):
    id: int
    number: str
    vehicle_type: Optional[str] = None
    fuel_consumable_id: Optional[int] = None
    fuel_consumable_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def inject_fuel_consumable_name(cls, data: Any) -> Any:
        # When building from an ORM object, pull name from the relationship
        if hasattr(data, "__dict__"):
            fc = getattr(data, "fuel_consumable", None)
            if fc is not None:
                data.__dict__["fuel_consumable_name"] = fc.name
        return data
