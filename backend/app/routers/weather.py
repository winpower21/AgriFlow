import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..api.openweathermap import get_location_details, get_weather_data
from ..schemas.weather import WeatherData

load_dotenv()
api_key = os.getenv("OPENWEATHERMAP_API_KEY")


class LocationSearchRequest(BaseModel):
    city: str


class LocationData(BaseModel):
    formatted_data: dict


router = APIRouter(
    prefix="/weather",
    responses={404: {"description": "Not found"}},
)


@router.get("/location-search", response_model=LocationData)
async def location_search(request: LocationSearchRequest):
    """
    Docstring for location_search

    :param request: Description
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
    Docstring for weather_data

    :param request: Description
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
