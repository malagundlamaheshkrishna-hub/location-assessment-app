import pytest
from unittest.mock import patch, MagicMock
import httpx
from fastapi.testclient import TestClient
from backend.main import app
from backend.scoring import compute_total_score_and_status
from backend.services.geocoder import geocode_address
from backend.services.elevation import get_elevation
from backend.services.weather import get_weather

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "health_check" in data


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_workflow_full_success():
    """Test full assessment workflow with geocoder, elevation, and weather succeeding."""
    mock_geo = {"available": True, "latitude": 39.7392, "longitude": -104.9903}
    mock_elev = {"available": True, "elevation": 5280.0}  # Above 5000 -> 0 points
    mock_weather = {"available": True, "temperature": 20.0}  # 15-25 -> 60 points

    with patch("backend.main.geocode_address", return_value=mock_geo), \
         patch("backend.main.get_elevation", return_value=mock_elev), \
         patch("backend.main.get_weather", return_value=mock_weather):

        response = client.post("/assessments", json={
            "label": "Denver Office",
            "address": "1437 Bannock St, Denver, CO"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["label"] == "Denver Office"
        assert data["address"] == "1437 Bannock St, Denver, CO"
        assert data["latitude"] == 39.7392
        assert data["longitude"] == -104.9903
        assert data["elevation"] == 5280.0
        assert data["temperature"] == 20.0
        assert data["elevation_score"] == 0.0
        assert data["temperature_score"] == 60.0
        assert data["total_score"] == 60.0
        assert data["status"] == "complete"

        # Verify GET /assessments and GET /assessments/{id}
        get_single = client.get(f"/assessments/{data['id']}")
        assert get_single.status_code == 200
        assert get_single.json()["total_score"] == 60.0

        get_all = client.get("/assessments")
        assert get_all.status_code == 200
        assert any(item["id"] == data["id"] for item in get_all.json())


def test_workflow_geocoder_failure():
    """Test workflow when geocoding fails: saves with status 'failed', does not call elevation/weather."""
    mock_geo = {"available": False, "error": "No matching address found."}

    with patch("backend.main.geocode_address", return_value=mock_geo), \
         patch("backend.main.get_elevation") as mock_elev, \
         patch("backend.main.get_weather") as mock_weather:

        response = client.post("/assessments", json={
            "label": "Unknown Island",
            "address": "999 Nowhere Land"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["latitude"] is None
        assert data["longitude"] is None
        assert data["elevation"] is None
        assert data["temperature"] is None
        assert data["elevation_score"] is None
        assert data["temperature_score"] is None
        assert data["total_score"] is None
        assert data["status"] == "failed"

        # Verify elevation and weather were never called
        mock_elev.assert_not_called()
        mock_weather.assert_not_called()


def test_workflow_partial_elevation_failure():
    """Test workflow when elevation fails but weather succeeds (status: partial, score not zeroed)."""
    mock_geo = {"available": True, "latitude": 37.7749, "longitude": -122.4194}
    mock_elev = {"available": False, "error": "USGS service timeout."}
    mock_weather = {"available": True, "temperature": 18.0}  # 15-25 -> 60 points

    with patch("backend.main.geocode_address", return_value=mock_geo), \
         patch("backend.main.get_elevation", return_value=mock_elev), \
         patch("backend.main.get_weather", return_value=mock_weather):

        response = client.post("/assessments", json={
            "label": "SF Bay Office",
            "address": "Market St, San Francisco, CA"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["elevation"] is None
        assert data["elevation_score"] is None
        assert data["temperature"] == 18.0
        assert data["temperature_score"] == 60.0
        assert data["total_score"] == 60.0  # ONLY available score, NOT (60+0)/2
        assert data["status"] == "partial"


def test_get_assessment_not_found():
    response = client.get("/assessments/9999999")
    assert response.status_code == 404


def test_calculate_elevation_score():
    from backend.scoring import calculate_elevation_score
    # 0-500 -> 40
    assert calculate_elevation_score(0) == 40.0
    assert calculate_elevation_score(250.0) == 40.0
    assert calculate_elevation_score(500.0) == 40.0
    # 501-1500 -> 30
    assert calculate_elevation_score(501.0) == 30.0
    assert calculate_elevation_score(1500.0) == 30.0
    # 1501-3000 -> 20
    assert calculate_elevation_score(1501.0) == 20.0
    assert calculate_elevation_score(3000.0) == 20.0
    # 3001-5000 -> 10
    assert calculate_elevation_score(3001.0) == 10.0
    assert calculate_elevation_score(5000.0) == 10.0
    # Above 5000 -> 0
    assert calculate_elevation_score(5001.0) == 0.0
    assert calculate_elevation_score(10000.0) == 0.0
    # Unavailable -> None
    assert calculate_elevation_score(None) is None


def test_calculate_temperature_score():
    from backend.scoring import calculate_temperature_score
    # 15-25 -> 60
    assert calculate_temperature_score(15.0) == 60.0
    assert calculate_temperature_score(20.0) == 60.0
    assert calculate_temperature_score(25.0) == 60.0
    # 10-14 or 26-30 -> 45
    assert calculate_temperature_score(10.0) == 45.0
    assert calculate_temperature_score(14.0) == 45.0
    assert calculate_temperature_score(26.0) == 45.0
    assert calculate_temperature_score(30.0) == 45.0
    # 5-9 or 31-35 -> 25
    assert calculate_temperature_score(5.0) == 25.0
    assert calculate_temperature_score(9.0) == 25.0
    assert calculate_temperature_score(31.0) == 25.0
    assert calculate_temperature_score(35.0) == 25.0
    # Below 5 or above 35 -> 10
    assert calculate_temperature_score(4.9) == 10.0
    assert calculate_temperature_score(-10.0) == 10.0
    assert calculate_temperature_score(36.0) == 10.0
    # Unavailable -> None
    assert calculate_temperature_score(None) is None


def test_calculate_total_score_and_summary():
    from backend.scoring import calculate_total_score, compute_assessment_scoring
    # Both available
    assert calculate_total_score(30.0, 45.0) == 75.0

    # Only elevation available (30 out of 40 available max points)
    assert calculate_total_score(30.0, None) == 30.0
    summary_elev = compute_assessment_scoring(elevation=1000.0, temperature=None)
    assert summary_elev["elevation_score"] == 30.0
    assert summary_elev["temperature_score"] is None
    assert summary_elev["total_score"] == 30.0
    assert summary_elev["max_available_points"] == 40.0
    assert summary_elev["status"] == "partial"

    # Only temperature available (45 out of 60 available max points)
    assert calculate_total_score(None, 45.0) == 45.0
    summary_temp = compute_assessment_scoring(elevation=None, temperature=12.0)
    assert summary_temp["elevation_score"] is None
    assert summary_temp["temperature_score"] == 45.0
    assert summary_temp["total_score"] == 45.0
    assert summary_temp["max_available_points"] == 60.0
    assert summary_temp["status"] == "partial"

    # Neither available
    assert calculate_total_score(None, None) is None
    summary_none = compute_assessment_scoring(elevation=None, temperature=None)
    assert summary_none["total_score"] is None
    assert summary_none["max_available_points"] == 0.0
    assert summary_none["status"] == "failed"


# --- Geocoder Tests ---

@pytest.mark.asyncio
async def test_geocoder_empty_address():
    result = await geocode_address("")
    assert result["available"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_geocoder_success_parsing():
    sample_response = {
        "result": {
            "addressMatches": [
                {
                    "coordinates": {
                        "x": -77.0365,
                        "y": 38.8977
                    }
                }
            ]
        }
    }
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await geocode_address("1600 Pennsylvania Ave NW, Washington, DC")
        assert result["available"] is True
        assert result["latitude"] == 38.8977
        assert result["longitude"] == -77.0365


@pytest.mark.asyncio
async def test_geocoder_no_match():
    sample_response = {
        "result": {
            "addressMatches": []
        }
    }
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await geocode_address("Fake non existent address")
        assert result["available"] is False
        assert "No matching address" in result["error"]


@pytest.mark.asyncio
async def test_geocoder_timeout():
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Connection timed out")):
        result = await geocode_address("Any Address")
        assert result["available"] is False
        assert "timed out" in result["error"]


@pytest.mark.asyncio
async def test_geocoder_http_error():
    request = httpx.Request("GET", "https://example.com")
    response = httpx.Response(500, request=request)
    with patch("httpx.AsyncClient.get", side_effect=httpx.HTTPStatusError("Server Error", request=request, response=response)):
        result = await geocode_address("Any Address")
        assert result["available"] is False
        assert "HTTP 500" in result["error"]


# --- Elevation Tests ---

@pytest.mark.asyncio
async def test_elevation_invalid_coords():
    result = await get_elevation(latitude=999.0, longitude=-104.0)
    assert result["available"] is False
    assert "Invalid coordinate range" in result["error"]


@pytest.mark.asyncio
async def test_elevation_success_parsing():
    sample_response = {
        "location": {"x": -104.9903, "y": 39.7392},
        "value": 5280.45,
        "units": "Feet"
    }
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"value": 5280.45}'
        mock_response.json.return_value = sample_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await get_elevation(latitude=39.7392, longitude=-104.9903)
        assert result["available"] is True
        assert result["elevation"] == 5280.45


@pytest.mark.asyncio
async def test_elevation_sentinel_out_of_bounds():
    sample_response = {
        "location": {"x": 0.0, "y": 0.0},
        "value": -1000000.0,
        "units": "Feet"
    }
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"value": -1000000.0}'
        mock_response.json.return_value = sample_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await get_elevation(latitude=0.0, longitude=0.0)
        assert result["available"] is False
        assert "out of coverage" in result["error"]
        assert "elevation" not in result  # Not converted to 0!


@pytest.mark.asyncio
async def test_elevation_empty_body():
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await get_elevation(latitude=0.0, longitude=0.0)
        assert result["available"] is False
        assert "empty response" in result["error"]


@pytest.mark.asyncio
async def test_elevation_timeout():
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Connection timed out")):
        result = await get_elevation(latitude=39.7392, longitude=-104.9903)
        assert result["available"] is False
        assert "timed out" in result["error"]


@pytest.mark.asyncio
async def test_elevation_http_error():
    request = httpx.Request("GET", "https://epqs.nationalmap.gov/v1/json")
    response = httpx.Response(503, request=request)
    with patch("httpx.AsyncClient.get", side_effect=httpx.HTTPStatusError("Service Unavailable", request=request, response=response)):
        result = await get_elevation(latitude=39.7392, longitude=-104.9903)
        assert result["available"] is False
        assert "HTTP 503" in result["error"]


# --- Weather Tests ---

@pytest.mark.asyncio
async def test_weather_invalid_coords():
    result = await get_weather(latitude=999.0, longitude=-122.0)
    assert result["available"] is False
    assert "Invalid coordinate range" in result["error"]


@pytest.mark.asyncio
async def test_weather_success_parsing():
    sample_response = {
        "latitude": 37.77,
        "longitude": -122.42,
        "current": {
            "time": "2026-10-02T10:45",
            "temperature_2m": 18.5
        }
    }
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await get_weather(latitude=37.77, longitude=-122.42)
        assert result["available"] is True
        assert result["temperature"] == 18.5


@pytest.mark.asyncio
async def test_weather_missing_temperature_field():
    sample_response = {
        "latitude": 37.77,
        "longitude": -122.42,
        "current": {}
    }
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await get_weather(latitude=37.77, longitude=-122.42)
        assert result["available"] is False
        assert "not found" in result["error"]
        assert "temperature" not in result  # Not converted to 0!


@pytest.mark.asyncio
async def test_weather_timeout():
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Connection timed out")):
        result = await get_weather(latitude=37.77, longitude=-122.42)
        assert result["available"] is False
        assert "timed out" in result["error"]


@pytest.mark.asyncio
async def test_weather_http_error():
    request = httpx.Request("GET", "https://api.open-meteo.com/v1/forecast")
    response = httpx.Response(500, request=request)
    with patch("httpx.AsyncClient.get", side_effect=httpx.HTTPStatusError("Internal Server Error", request=request, response=response)):
        result = await get_weather(latitude=37.77, longitude=-122.42)
        assert result["available"] is False
        assert "HTTP 500" in result["error"]
