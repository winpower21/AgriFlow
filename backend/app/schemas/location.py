from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LocationSchema(BaseModel):
    """Schema for location data."""

    city: str
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)


class LocationCreateSchema(LocationSchema):
    """Schema for location data."""

    id: int
    plantation_id: int
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
