"""
Location Pydantic schemas.

Defines schemas for geographic location data associated with plantations.
Locations store city, state, country, and GPS coordinates (latitude/longitude).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LocationSchema(BaseModel):
    """Base location schema used for embedding location data inside other schemas.

    This schema is used both as a standalone response body and as a nested
    field within PlantationCreate / PlantationUpdate requests.

    Fields:
        city:      Name of the city or town.
        state:     Optional state or province.
        country:   Optional country name or ISO code.
        latitude:  GPS latitude in decimal degrees.
        longitude: GPS longitude in decimal degrees.
    """

    city: str
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)


class LocationCreateSchema(LocationSchema):
    """Full API response schema for a location record stored in the database.

    Extends LocationSchema with server-managed fields including the primary
    key, the owning plantation FK, default flag, and audit timestamps.

    Note: Despite the 'Create' suffix, this schema is currently used as a
    *response* model (it contains ``id`` and ``created_at``).

    Fields:
        id:             Server-generated primary key.
        plantation_id:  FK to the plantation this location belongs to.
        is_default:     Whether this is the plantation's default location.
        created_at:     Timestamp when the record was created.
        updated_at:     Timestamp of the last update (nullable).
    """

    id: int
    plantation_id: int
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LocationDetailSchema(BaseModel):
    """Response schema for a location row that includes the database id.

    Used by /locations/resolve and /api/weather/locations so the
    frontend can store location_id after resolving a Google place.
    """

    id: int
    city: str
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)
