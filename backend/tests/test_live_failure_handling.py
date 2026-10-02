import pytest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.elevation import get_elevation
from backend.services.weather import get_weather
from backend.services.geocoder import geocode_address

client = TestClient(app)

MOCK_GEO_SUCCESS = {"available": True, "latitude": 38.8977, "longitude": -77.0365}


def test_invalid_elevation_url_workflow():
    """
    Failure handling verification:
    When elevation service returns unavailable:
    1. Submit a valid location.
    2. Elevation API is unavailable.
    3. Confirm assessment is still saved.
    4. Confirm temperature is still displayed / available.
    5. Confirm elevation is None (frontend displays 'Unavailable').
    6. Confirm elevation is NOT shown as 0.
    """
    mock_weather = {"available": True, "temperature": 22.5}
    with patch("backend.main.geocode_address", return_value=MOCK_GEO_SUCCESS), \
         patch("backend.main.get_elevation", return_value={"available": False, "error": "Service unavailable"}), \
         patch("backend.main.get_weather", return_value=mock_weather):
        response = client.post("/assessments", json={
            "label": "Failure Test Location",
            "address": "1600 Pennsylvania Avenue NW, Washington, DC"
        })
        assert response.status_code == 201
        data = response.json()
        
        # 3. Confirm assessment is saved
        assert data["id"] is not None
        assert data["address"] == "1600 Pennsylvania Avenue NW, Washington, DC"
        
        # Coordinates from geocoder should succeed
        assert data["latitude"] == 38.8977
        assert data["longitude"] == -77.0365
        
        # 4. Confirm temperature is still fetched and available (22.5°C -> 60.0 pts)
        assert data["temperature"] == 22.5
        assert data["temperature_score"] == 60.0
        
        # 5 & 6. Confirm elevation is None (NOT 0)
        assert data["elevation"] is None
        assert data["elevation_score"] is None
        
        # Total score should only be based on temperature, not penalized by 0
        assert data["total_score"] == 60.0
        assert data["status"] == "partial"
        
        # Verify persisted in SQLite
        get_res = client.get(f"/assessments/{data['id']}")
        assert get_res.status_code == 200
        saved = get_res.json()
        assert saved["id"] == data["id"]
        assert saved["elevation"] is None
        assert saved["temperature"] == 22.5
        assert saved["total_score"] == 60.0
        assert saved["status"] == "partial"


def test_restored_elevation_url_workflow():
    """
    Verification of complete assessment workflow when both services succeed.
    """
    mock_elev = {"available": True, "elevation": 54.0}
    mock_weather = {"available": True, "temperature": 20.0}
    with patch("backend.main.geocode_address", return_value=MOCK_GEO_SUCCESS), \
         patch("backend.main.get_elevation", return_value=mock_elev), \
         patch("backend.main.get_weather", return_value=mock_weather):
        response = client.post("/assessments", json={
            "label": "Restored URL Test",
            "address": "1600 Pennsylvania Avenue NW, Washington, DC"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["latitude"] == 38.8977
        assert data["longitude"] == -77.0365
        assert data["elevation"] == 54.0
        assert data["temperature"] == 20.0
        assert data["elevation_score"] == 40.0
        assert data["temperature_score"] == 60.0
        assert data["total_score"] == 100.0
        assert data["status"] == "complete"


@pytest.mark.asyncio
async def test_graceful_timeout_handling_service_level():
    """Verify that timeouts in each external service are caught and handled gracefully without crashing."""
    
    # 1. Geocoder Timeout
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Census Geocoder timed out")):
        geo_result = await geocode_address("1600 Pennsylvania Ave NW, Washington, DC")
        assert geo_result["available"] is False
        assert "timed out" in geo_result["error"].lower()
        
    # 2. Elevation Timeout
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("USGS EPQS timed out")):
        elev_result = await get_elevation(38.8977, -77.0365)
        assert elev_result["available"] is False
        assert "timed out" in elev_result["error"].lower()
        assert "elevation" not in elev_result
        
    # 3. Weather Timeout
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Open-Meteo timed out")):
        weather_result = await get_weather(38.8977, -77.0365)
        assert weather_result["available"] is False
        assert "timed out" in weather_result["error"].lower()
        assert "temperature" not in weather_result


def test_workflow_elevation_timeout_handled_gracefully():
    """Verify full POST /assessments workflow when elevation service times out."""
    mock_weather = {"available": True, "temperature": 18.0}
    with patch("backend.main.geocode_address", return_value=MOCK_GEO_SUCCESS), \
         patch("backend.main.get_elevation", return_value={"available": False, "error": "Request to USGS Elevation service timed out after 10.0s."}), \
         patch("backend.main.get_weather", return_value=mock_weather):
        response = client.post("/assessments", json={
            "label": "Elevation Timeout Test",
            "address": "1600 Pennsylvania Avenue NW, Washington, DC"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["elevation"] is None
        assert data["elevation_score"] is None
        assert data["temperature"] == 18.0
        assert data["temperature_score"] == 60.0
        assert data["total_score"] == 60.0
        assert data["status"] == "partial"


def test_workflow_weather_timeout_handled_gracefully():
    """Verify full POST /assessments workflow when weather service times out."""
    with patch("backend.main.geocode_address", return_value=MOCK_GEO_SUCCESS), \
         patch("backend.main.get_weather", return_value={"available": False, "error": "Request to Open-Meteo timed out after 10.0s."}), \
         patch("backend.main.get_elevation", return_value={"available": True, "elevation": 120.0}):
        response = client.post("/assessments", json={
            "label": "Weather Timeout Test",
            "address": "1600 Pennsylvania Avenue NW, Washington, DC"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["elevation"] == 120.0
        assert data["elevation_score"] == 40.0
        assert data["temperature"] is None
        assert data["temperature_score"] is None
        assert data["total_score"] == 40.0
        assert data["status"] == "partial"


def test_workflow_geocoder_timeout_handled_gracefully():
    """Verify full POST /assessments workflow when geocoding service times out."""
    with patch("backend.main.geocode_address", return_value={"available": False, "error": "Request to US Census Geocoder timed out after 10.0s."}):
        response = client.post("/assessments", json={
            "label": "Geocoder Timeout Test",
            "address": "1600 Pennsylvania Avenue NW, Washington, DC"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["latitude"] is None
        assert data["longitude"] is None
        assert data["elevation"] is None
        assert data["temperature"] is None
        assert data["status"] == "failed"
