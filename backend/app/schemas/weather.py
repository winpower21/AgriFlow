from datetime import datetime

from pydantic import BaseModel, ConfigDict

# from .role import Role


class WeatherSchema(BaseModel):
    """Schema for weather data."""

    id: int
    location_id: int
    timestamp: datetime
    temperature_c: float
    humidity_percent: float
    precipitation_mm: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
