"""Weather data source (OpenWeatherMap or mock fallback)."""

from __future__ import annotations

from typing import Any

import httpx

from src.config import (
    DEFAULT_LAT,
    DEFAULT_LOCATION_NAME,
    DEFAULT_LON,
    OPENWEATHER_API_KEY,
)


async def fetch_weather(
    lat: float = DEFAULT_LAT,
    lon: float = DEFAULT_LON,
    location_name: str = DEFAULT_LOCATION_NAME,
) -> dict[str, Any]:
    if not OPENWEATHER_API_KEY:
        return {
            "source": "mock",
            "location": location_name,
            "lat": lat,
            "lon": lon,
            "temp_c": 18.5,
            "humidity_pct": 62,
            "wind_mps": 3.2,
            "condition": "partly cloudy",
            "rain_mm_1h": 0.0,
        }

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    return {
        "source": "openweathermap",
        "location": data.get("name") or location_name,
        "lat": lat,
        "lon": lon,
        "temp_c": data["main"]["temp"],
        "humidity_pct": data["main"]["humidity"],
        "wind_mps": data.get("wind", {}).get("speed", 0.0),
        "condition": data["weather"][0]["description"] if data.get("weather") else "unknown",
        "rain_mm_1h": (data.get("rain") or {}).get("1h", 0.0),
    }
