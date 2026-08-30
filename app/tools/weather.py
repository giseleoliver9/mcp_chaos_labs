from typing import Any


def weather_tool(payload: dict[str, Any]) -> dict[str, Any]:
    location = payload["location"]
    return {
        "status": "success",
        "result": {
            "location": location,
            "temperature_c": 24,
            "condition": "partly cloudy",
        },
    }


def cached_weather_tool(payload: dict[str, Any]) -> dict[str, Any]:
    location = payload["location"]
    return {
        "status": "success",
        "result": {
            "location": location,
            "temperature_c": None,
            "condition": "cached forecast unavailable",
        },
    }
