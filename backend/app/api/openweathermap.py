import httpx
from fastapi import HTTPException

from app.config import settings


async def get_location_details(city: str, api_key: str) -> dict:
    """
    Fetch location details from OpenWeatherMap API.
    Returns a dictionary with latitude and longitude.
    """
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=4&appid={settings.OPENWEATHERMAP_API_KEY}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch location details"
        )

    data = response.json()
    if not data:
        raise HTTPException(status_code=404, detail="Location not found")

    formatted_data = {}
    for i in data:
        formatted_data[i["name"]] = {
            "state": i.get("state"),
            "country": i.get("country"),
            "latitude": i.get("lat"),
            "longitude": i.get("lon"),
        }

    return formatted_data


async def get_weather_data(latitude: float, longitude: float, api_key: str) -> dict:
    """
    Fetch weather data from OpenWeatherMap API.
    Returns a dictionary with weather information.
    """
    url = f"{settings.OPENWEATHERMAP_API_URL}?lat={latitude}&lon={longitude}&appid={settings.OPENWEATHERMAP_API_KEY}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch weather data"
        )

    data = response.json()
    if not data:
        raise HTTPException(status_code=404, detail="Weather data not found")

    formatted_data = {
        "temperature": data.get("main", {}).get("temp"),
        "humidity": data.get("main", {}).get("humidity"),
        "description": data.get("weather", [{}])[0].get("description"),
    }

    return formatted_data


async def get_forecast_data(latitude: float, longitude: float, api_key: str) -> dict:
    """
    Fetch forecast data from OpenWeatherMap API.
    Returns a dictionary with forecast information.
    """
    url = f"{settings.OPENWEATHERMAP_API_URL}?lat={latitude}&lon={longitude}&appid={settings.OPENWEATHERMAP_API_KEY}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch forecast data"
        )

    data = response.json()
    if not data:
        raise HTTPException(status_code=404, detail="Forecast data not found")

    formatted_data = {
        "temperature": data.get("main", {}).get("temp"),
        "humidity": data.get("main", {}).get("humidity"),
        "description": data.get("weather", [{}])[0].get("description"),
    }

    return formatted_data
