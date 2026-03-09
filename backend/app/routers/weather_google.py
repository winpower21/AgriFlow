"""
Weather & Location Search endpoints using Google Maps Platform APIs.

All outbound HTTP calls are delegated to ``app.api.googleapi`` — this
router only handles FastAPI routing, query validation, and response shaping.

Endpoints
---------
GET /api/weather/search-locations    — Autocomplete location search.
GET /api/weather/place-details       — Resolve Place ID to lat/lng.
GET /api/weather/current             — Current weather for a lat/lng.
GET /api/weather/forecast            — Hourly forecast for a lat/lng.

Authentication: none (public endpoints).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..api.googleapi import (
    get_current_weather,
    get_hourly_forecast,
    get_place_details,
    search_places,
)
from ..core.dependencies import get_current_user
from ..crud.plantation import PlantationService
from ..database import get_db
from ..models.location import Location
from ..schemas.location import LocationDetailSchema
from ..schemas.weather import WeatherSchema

router = APIRouter(
    prefix="/api/weather",
    tags=["weather"],
    responses={404: {"description": "Not found"}},
)


@router.get("/search-locations")
async def search_locations(
    query: str = Query(..., min_length=2, description="Location search text"),
):
    """
    Proxy to Google Places Autocomplete filtered to geographic regions.
    Returns city/district/state suggestions — no businesses or buildings.
    """
    return {"predictions": await search_places(query)}


@router.get("/place-details")
async def place_details(
    place_id: str = Query(..., description="Google Place ID"),
):
    """Fetch lat/lng and formatted address for a Google Place ID."""
    return await get_place_details(place_id)


@router.get("/current")
async def current_conditions(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """Current weather conditions for a lat/lng pair."""
    return await get_current_weather(lat, lng)


@router.get("/forecast")
async def hourly_forecast(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    hours: int = Query(24, ge=1, le=240, description="Forecast hours"),
):
    """Hourly weather forecast for a lat/lng pair."""
    return await get_hourly_forecast(lat, lng, hours)


# ── Location-centric weather endpoints ───────────────────────────────────────

location_weather_router = APIRouter(
    prefix="/api/weather",
    tags=["weather"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@location_weather_router.get("/locations", response_model=list[LocationDetailSchema])
def list_weather_locations(db: Session = Depends(get_db)):
    """Return all location rows for the WeatherView saved-locations list.

    Returns every row in the locations table, ordered by city name.
    Includes plantation-linked locations — the WeatherView shows all of them.
    """
    return db.query(Location).order_by(Location.city).all()


@location_weather_router.get(
    "/by-location/{location_id}", response_model=WeatherSchema
)
async def get_weather_by_location(
    location_id: int, db: Session = Depends(get_db)
):
    """Return weather for a location using a 6-hour TTL cache.

    Cache hit  → returns the most recent Weather row fetched within 6 hours.
    Cache miss → calls Google Weather API, persists a new append-only row,
                 and returns it.

    Returns 404 if the location does not exist.
    """
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    service = PlantationService(db)
    cached = service.get_cached_weather(location_id)
    if cached:
        return cached

    # Cache miss — fetch from Google and persist
    current = await get_current_weather(loc.latitude, loc.longitude)
    hourly = await get_hourly_forecast(loc.latitude, loc.longitude, hours=24)
    raw = {"current": current, "hourly": hourly}
    return service.save_weather(location_id, raw, is_manual=False)


@location_weather_router.post(
    "/by-location/{location_id}/refresh",
    response_model=WeatherSchema,
    status_code=201,
)
async def refresh_weather_by_location(
    location_id: int, db: Session = Depends(get_db)
):
    """Manually refresh weather — always fetches fresh data (is_manual=True).

    Ignores the 6-hour TTL. Previous rows are preserved (append-only).
    Returns 404 if the location does not exist.
    """
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    service = PlantationService(db)
    current = await get_current_weather(loc.latitude, loc.longitude)
    hourly = await get_hourly_forecast(loc.latitude, loc.longitude, hours=24)
    raw = {"current": current, "hourly": hourly}
    return service.save_weather(location_id, raw, is_manual=True)
