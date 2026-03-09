"""
Weather router using the OpenWeatherMap API.

Provides location search (geocoding) and current weather data endpoints
backed by the ``app.api.openweathermap`` HTTP client module.

Endpoints
---------
GET /weather/location-search  — Geocode a city name to lat/lng via
                                 OpenWeatherMap's direct geocoding API.
GET /weather/weatherdata      — Fetch current weather for a city.

Authentication / authorisation
------------------------------
**No authentication is required** — this router has no auth dependencies.
(It also lacks a ``tags`` keyword, so endpoints appear under *default* in
the OpenAPI docs.)

Known issues / status
---------------------
- This router is currently **broken / incomplete**.
- Both endpoints accept a ``LocationSearchRequest`` body on GET, which
  violates HTTP conventions (GET should not have a request body).
- ``get_weather_data()`` expects ``(latitude, longitude, api_key)`` but
  ``weather_data()`` passes a city name string, causing a runtime error.
- The API key is loaded from ``.env`` via ``dotenv`` at module level rather
  than using the app-wide ``settings`` object.
- Consider using ``weather_google.py`` instead for a working implementation.
"""

import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..api.openweathermap import get_location_details, get_weather_data
from ..schemas.weather import WeatherData

# Load the OpenWeatherMap API key from the .env file at module import time.
# NOTE: This duplicates the config pattern — prefer ``app.config.settings``
# for consistency.
load_dotenv()
api_key = os.getenv("OPENWEATHERMAP_API_KEY")


class LocationSearchRequest(BaseModel):
    """Inline request model for location-based queries. Contains a single
    ``city`` field (name of the city to search for)."""
    city: str


class LocationData(BaseModel):
    """Inline response model wrapping the geocoded location dictionary."""
    formatted_data: dict


# No auth dependency and no tags — endpoints appear under the default group
# in the OpenAPI docs.
router = APIRouter(
    prefix="/weather",
    responses={404: {"description": "Not found"}},
)


@router.get("/location-search", response_model=LocationData)
async def location_search(request: LocationSearchRequest):
    """
    Geocode a city name to location details (lat/lng, state, country) via
    OpenWeatherMap's direct geocoding API.

    **Auth:** none (public endpoint).

    NOTE: Uses a request body on GET, which is non-standard.  The city name
    is lowered before being sent to the upstream API.  Returns up to 4
    matching locations.

    :param request: Body containing the city name to search for.
    :type request: LocationSearchRequest
    """
    city = request.city.lower()
    if not city:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="City name is required",
        )

    try:
        formatted_data = get_location_details(city, api_key=api_key)
        return formatted_data
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Error fetching location details: {e.detail}",
        )


@router.get("/weatherdata", response_model=WeatherData)
async def weather_data(request: LocationSearchRequest):
    """
    Fetch current weather data for a city via OpenWeatherMap.

    **Auth:** none (public endpoint).

    NOTE: This endpoint is currently **broken** — ``get_weather_data()``
    expects ``(latitude, longitude, api_key)`` but this handler passes the
    city name as the first argument, which will cause a runtime error.

    :param request: Body containing the city name.
    :type request: LocationSearchRequest
    """
    city = request.city.lower()
    if not city:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="City name is required",
        )

    try:
        formatted_data = get_weather_data(city, api_key=api_key)
        return formatted_data
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Error fetching weather data: {e.detail}",
        )
