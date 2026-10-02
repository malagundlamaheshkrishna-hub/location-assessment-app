import logging
from typing import Dict, Any
import httpx

logger = logging.getLogger(__name__)

CENSUS_GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
USER_AGENT = "LocationAssessmentTool/1.0"
TIMEOUT_SECONDS = 10.0


async def geocode_address(address: str) -> Dict[str, Any]:
    """
    Geocodes a US address using the US Census Bureau Geocoding API.

    Returns:
        On success:
            {"available": True, "latitude": float, "longitude": float}
        On failure / no match:
            {"available": False, "error": str}
    """
    if not address or not address.strip():
        return {
            "available": False,
            "error": "Address string cannot be empty."
        }

    params = {
        "address": address.strip(),
        "benchmark": "Public_AR_Current",
        "format": "json"
    }
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(
                CENSUS_GEOCODER_URL,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

        # Extract address matches from Census response
        matches = data.get("result", {}).get("addressMatches", [])
        if not matches:
            return {
                "available": False,
                "error": "No matching address found in US Census Geocoder."
            }

        first_match = matches[0]
        coordinates = first_match.get("coordinates", {})
        
        # Census Geocoder returns 'x' as Longitude and 'y' as Latitude
        lon = coordinates.get("x")
        lat = coordinates.get("y")

        if lat is None or lon is None:
            return {
                "available": False,
                "error": "Census Geocoder returned match without coordinates."
            }

        return {
            "available": True,
            "latitude": float(lat),
            "longitude": float(lon)
        }

    except httpx.TimeoutException:
        logger.warning(f"Timeout connecting to US Census Geocoder for address: {address}")
        return {
            "available": False,
            "error": f"Request to US Census Geocoder timed out after {TIMEOUT_SECONDS}s."
        }
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error from US Census Geocoder: {e.response.status_code}")
        return {
            "available": False,
            "error": f"US Census Geocoder returned HTTP {e.response.status_code}."
        }
    except httpx.RequestError as e:
        logger.warning(f"Connection error to US Census Geocoder: {str(e)}")
        return {
            "available": False,
            "error": f"Failed to connect to US Census Geocoder: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error during geocoding: {str(e)}", exc_info=True)
        return {
            "available": False,
            "error": f"An unexpected geocoding error occurred: {str(e)}"
        }
