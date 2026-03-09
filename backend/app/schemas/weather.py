"""
Weather Pydantic schemas.

WeatherSchema reflects the refactored append-only Weather model that
stores the full Google Weather API response as JSONB rather than
individual numeric columns.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WeatherSchema(BaseModel):
    """API response schema for an append-only weather record.

    Fields:
        id:          Server-generated primary key.
        location_id: FK to the location this observation covers.
        fetched_at:  When this record was fetched from the Google Weather API.
        is_manual:   True if the user explicitly triggered the refresh.
        raw_json:    Full raw Google Weather API JSON response.
    """

    id: int
    location_id: int
    fetched_at: datetime
    is_manual: bool
    raw_json: dict

    model_config = ConfigDict(from_attributes=True)
