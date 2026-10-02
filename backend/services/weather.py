import logging
from typing import Dict, Any, Union
import httpx

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
USER_AGENT = "LocationAssessmentTool/1.0"
TIMEOUT_SECONDS = 10.0


async def get_weather(latitude: Union[float, int], longitude: Union[float, int]) -> Dict[str, Any]:
    """
    Fetches the current temperature (temperature_2m) using the Open-Meteo forecast API.

    Returns:
        On success:
            {"available": True, "temperature": float}
        On failure / unavailable:
            {"available": False, "error": str}
            
    Note: Does NOT convert unavailable temperature to 0.
    """
    # Validate coordinate inputs
    try:
        lat = float(latitude)
        lon = float(longitude)
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return {
                "available": False,
                "error": f"Invalid coordinate range: latitude ({lat}), longitude ({lon})."
            }
    except (TypeError, ValueError):
        return {
            "available": False,
            "error": "Latitude and Longitude must be valid numbers."
        }

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m"
    }
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(
                OPEN_METEO_URL,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

        # Validate response structure
        if not isinstance(data, dict):
            return {
                "available": False,
                "error": "Unexpected response format from Open-Meteo API."
            }

        current_data = data.get("current")
        if not isinstance(current_data, dict):
            return {
                "available": False,
                "error": "Current weather block missing in Open-Meteo response."
            }

        temp_val = current_data.get("temperature_2m")
        if temp_val is None:
            return {
                "available": False,
                "error": "Temperature value (temperature_2m) not found in Open-Meteo response."
            }

        return {
            "available": True,
            "temperature": round(float(temp_val), 2)
        }

    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid temperature data from Open-Meteo: {str(e)}")
        return {
            "available": False,
            "error": f"Failed to parse Open-Meteo response: {str(e)}"
        }
    except httpx.TimeoutException:
        logger.warning(f"Timeout connecting to Open-Meteo for ({latitude}, {longitude})")
        return {
            "available": False,
            "error": f"Request to Open-Meteo timed out after {TIMEOUT_SECONDS}s."
        }
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error from Open-Meteo: {e.response.status_code}")
        return {
            "available": False,
            "error": f"Open-Meteo API returned HTTP {e.response.status_code}."
        }
    except httpx.RequestError as e:
        logger.warning(f"Connection error to Open-Meteo: {str(e)}")
        return {
            "available": False,
            "error": f"Failed to connect to Open-Meteo API: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error during weather fetch: {str(e)}", exc_info=True)
        return {
            "available": False,
            "error": f"An unexpected weather service error occurred: {str(e)}"
        }
