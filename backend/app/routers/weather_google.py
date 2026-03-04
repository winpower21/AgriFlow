"""
Weather & Location Search endpoints using Google Maps Platform APIs.

Standalone router — no database models or dependencies required.
Uses Google Places Autocomplete (Legacy) for location search
and Google Weather API for current conditions + daily forecast.
"""

import httpx
from fastapi import APIRouter, HTTPException, Query

from ..config import settings

router = APIRouter(
    prefix="/api/weather",
    tags=["weather"],
    responses={404: {"description": "Not found"}},
)

GOOGLE_PLACES_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
GOOGLE_PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
GOOGLE_WEATHER_CURRENT_URL = (
    "https://weather.googleapis.com/v1/currentConditions:lookup"
)
GOOGLE_WEATHER_FORECAST_URL = "https://weather.googleapis.com/v1/forecast/days:lookup"


@router.get("/search-locations")
async def search_locations(
    query: str = Query(..., min_length=2, description="Location search text"),
):
    """
    Proxy to Google Places Autocomplete filtered to geographic regions.
    Returns city/district/state suggestions — no businesses or buildings.
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(
            status_code=500,
            detail=f"Google Maps API key not configured{settings.GOOGLE_MAPS_API_KEY}",
        )

    params = {
        "input": query,
        "types": "(regions)",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_PLACES_URL, params=params, timeout=10)

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Google Places API error")

    data = resp.json()

    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise HTTPException(
            status_code=502,
            detail=f"Google Places API returned: {data.get('status')}",
        )

    predictions = data.get("predictions", [])
    results = []
    for p in predictions:
        results.append(
            {
                "place_id": p.get("place_id"),
                "description": p.get("description"),
                "main_text": p.get("structured_formatting", {}).get("main_text"),
                "secondary_text": p.get("structured_formatting", {}).get(
                    "secondary_text"
                ),
                "types": p.get("types", []),
            }
        )

    return {"predictions": results}


@router.get("/place-details")
async def place_details(
    place_id: str = Query(..., description="Google Place ID"),
):
    """
    Fetch lat/lng and formatted address for a place ID.
    Used after user selects a location from autocomplete.
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(
            status_code=500, detail="Google Maps API key not configured"
        )

    params = {
        "place_id": place_id,
        "fields": "geometry,formatted_address,name,address_components",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_PLACE_DETAILS_URL, params=params, timeout=10)

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Google Place Details API error")

    data = resp.json()

    if data.get("status") != "OK":
        raise HTTPException(
            status_code=502,
            detail=f"Place Details returned: {data.get('status')}",
        )

    result = data.get("result", {})
    location = result.get("geometry", {}).get("location", {})

    return {
        "name": result.get("name"),
        "formatted_address": result.get("formatted_address"),
        "latitude": location.get("lat"),
        "longitude": location.get("lng"),
        "address_components": result.get("address_components", []),
    }


@router.get("/current")
async def current_conditions(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """
    Proxy to Google Weather API — current conditions for a lat/lng.
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(
            status_code=500, detail="Google Maps API key not configured"
        )

    params = {
        "key": settings.GOOGLE_MAPS_API_KEY,
        "location.latitude": lat,
        "location.longitude": lng,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_WEATHER_CURRENT_URL, params=params, timeout=10)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Google Weather API error: {resp.status_code}",
        )

    return resp.json()


@router.get("/forecast")
async def daily_forecast(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    days: int = Query(5, ge=1, le=10, description="Number of forecast days"),
):
    """
    Proxy to Google Weather API — daily forecast for a lat/lng.
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(
            status_code=500, detail="Google Maps API key not configured"
        )

    params = {
        "key": settings.GOOGLE_MAPS_API_KEY,
        "location.latitude": lat,
        "location.longitude": lng,
        "days": days,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_WEATHER_FORECAST_URL, params=params, timeout=10)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Google Weather API error: {resp.status_code}",
        )

    return resp.json()
