import logging
from typing import Dict, Any, Union
import httpx

logger = logging.getLogger(__name__)

USGS_EPQS_URL = "https://epqs.nationalmap.gov/v1/json"
USER_AGENT = "LocationAssessmentTool/1.0"
TIMEOUT_SECONDS = 10.0

# USGS EPQS no-data sentinel values (e.g. ocean, out-of-coverage bounds)
INVALID_ELEVATION_SENTINELS = {-1000000, -999999, -1000000.0, -999999.0}


async def get_elevation(latitude: Union[float, int], longitude: Union[float, int]) -> Dict[str, Any]:
    """
    Fetches elevation in feet for given latitude and longitude using USGS EPQS API.

    Returns:
        On success:
            {"available": True, "elevation": float}
        On failure / unavailable / out of coverage:
            {"available": False, "error": str}
            
    Note: Does NOT convert unavailable elevation to 0.
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
        "x": lon,
        "y": lat,
        "units": "Feet",
        "output": "json"
    }
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(
                USGS_EPQS_URL,
                params=params,
                headers=headers
            )
            response.raise_for_status()

            # Handle empty body responses (e.g. out of coverage returns empty 200)
            if not response.text or not response.text.strip():
                return {
                    "available": False,
                    "error": "USGS Elevation service returned an empty response (point may be out of coverage)."
                }

            data = response.json()

        # Validate response format
        if not isinstance(data, dict):
            return {
                "available": False,
                "error": "Unexpected response format from USGS Elevation service."
            }

        # USGS EPQS v1 returns elevation under 'value' or 'elevation'
        raw_val = data.get("value")
        if raw_val is None:
            raw_val = data.get("elevation")

        if raw_val is None:
            return {
                "available": False,
                "error": "Elevation value not found in USGS service response."
            }

        elevation_val = float(raw_val)

        # Check for USGS out-of-bounds/no-data sentinels (-1000000, -999999)
        if elevation_val in INVALID_ELEVATION_SENTINELS or elevation_val < -2000.0:
            return {
                "available": False,
                "error": "Elevation data unavailable for these coordinates (out of coverage)."
            }

        return {
            "available": True,
            "elevation": round(elevation_val, 2)
        }

    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid JSON or elevation data format from USGS: {str(e)}")
        return {
            "available": False,
            "error": f"Failed to parse elevation response: {str(e)}"
        }
    except httpx.TimeoutException:
        logger.warning(f"Timeout connecting to USGS Elevation service for ({latitude}, {longitude})")
        return {
            "available": False,
            "error": f"Request to USGS Elevation service timed out after {TIMEOUT_SECONDS}s."
        }
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error from USGS Elevation service: {e.response.status_code}")
        return {
            "available": False,
            "error": f"USGS Elevation service returned HTTP {e.response.status_code}."
        }
    except httpx.RequestError as e:
        logger.warning(f"Connection error to USGS Elevation service: {str(e)}")
        return {
            "available": False,
            "error": f"Failed to connect to USGS Elevation service: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error during elevation lookup: {str(e)}", exc_info=True)
        return {
            "available": False,
            "error": f"An unexpected elevation service error occurred: {str(e)}"
        }
