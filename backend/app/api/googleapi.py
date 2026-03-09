"""
Google Maps Platform API helpers.

All outbound HTTP calls to Google APIs are made here, mirroring the
openweathermap.py pattern.  Import these functions from routers and
services — never make raw httpx calls to Google outside this module.

Functions
---------
search_places        — Google Places Autocomplete (regions only).
get_place_details    — Resolve a Place ID to lat/lng + address parts.
get_current_weather  — Google Weather current conditions for a lat/lng.
get_hourly_forecast  — Google Weather hourly forecast for a lat/lng.
"""

import httpx
from fastapi import HTTPException

from app.config import settings

# ── Google API base URLs ──────────────────────────────────────────────────────
_PLACES_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
_PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
_WEATHER_CURRENT_URL = "https://weather.googleapis.com/v1/currentConditions:lookup"
_WEATHER_HOURLY_URL = "https://weather.googleapis.com/v1/forecast/hours:lookup"


def _require_key() -> str:
    """Return the Google Maps API key or raise 500 if not configured."""
    key = settings.GOOGLE_MAPS_API_KEY
    if not key:
        raise HTTPException(status_code=500, detail="Google Maps API key not configured")
    return key


async def search_places(query: str) -> list[dict]:
    """
    Call Google Places Autocomplete filtered to geographic regions.

    Returns a list of predictions, each with:
        place_id, description, main_text, secondary_text, types

    Raises 502 if Google returns a non-200 or error status code.
    """
    key = _require_key()
    params = {
        "input": query,
        "types": "(regions)",
        "key": key,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_PLACES_URL, params=params, timeout=10)

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Google Places API error")

    data = resp.json()
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise HTTPException(
            status_code=502,
            detail=f"Google Places API returned: {data.get('status')}",
        )

    results = []
    for p in data.get("predictions", []):
        results.append({
            "place_id": p.get("place_id"),
            "description": p.get("description"),
            "main_text": p.get("structured_formatting", {}).get("main_text"),
            "secondary_text": p.get("structured_formatting", {}).get("secondary_text"),
            "types": p.get("types", []),
        })
    return results


async def get_place_details(place_id: str) -> dict:
    """
    Resolve a Google Place ID to lat/lng and address components.

    Returns: { name, formatted_address, latitude, longitude, address_components }

    Raises 502 if Google returns a non-200 or non-OK status.
    """
    key = _require_key()
    params = {
        "place_id": place_id,
        "fields": "geometry,formatted_address,name,address_components",
        "key": key,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_PLACE_DETAILS_URL, params=params, timeout=10)

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Google Place Details API error")

    data = resp.json()
    if data.get("status") != "OK":
        raise HTTPException(
            status_code=502,
            detail=f"Place Details returned: {data.get('status')}",
        )

    result = data.get("result", {})
    loc = result.get("geometry", {}).get("location", {})
    return {
        "name": result.get("name"),
        "formatted_address": result.get("formatted_address"),
        "latitude": loc.get("lat"),
        "longitude": loc.get("lng"),
        "address_components": result.get("address_components", []),
    }


async def get_current_weather(latitude: float, longitude: float) -> dict:
    """
    Fetch current weather conditions from Google Weather API.

    Returns the raw JSON response from currentConditions:lookup.
    Raises 502 on upstream failure.
    """
    key = _require_key()
    params = {
        "key": key,
        "location.latitude": latitude,
        "location.longitude": longitude,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_WEATHER_CURRENT_URL, params=params, timeout=10)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Google Weather API error: {resp.status_code}",
        )
    return resp.json()


async def get_hourly_forecast(latitude: float, longitude: float, hours: int = 24) -> dict:
    """
    Fetch hourly weather forecast from Google Weather API.

    Args:
        latitude:  Decimal degrees latitude.
        longitude: Decimal degrees longitude.
        hours:     Number of forecast hours to return (default 24, max 240).

    Returns the raw JSON response from forecast/hours:lookup.
    Raises 502 on upstream failure.
    """
    key = _require_key()
    params = {
        "key": key,
        "location.latitude": latitude,
        "location.longitude": longitude,
        "hours": hours,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_WEATHER_HOURLY_URL, params=params, timeout=10)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Google Weather hourly API error: {resp.status_code}",
        )
    return resp.json()
