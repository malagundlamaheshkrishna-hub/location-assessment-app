"""
Pytest unit tests for the Location Assessment Tool scoring engine.
"""

from backend.scoring import (
    calculate_elevation_score,
    calculate_temperature_score,
    calculate_total_score,
    compute_assessment_scoring,
)


# --- 1 to 5: Elevation Tests ---

def test_elevation_300_ft_returns_40():
    """1. Elevation 300 ft returns 40."""
    assert calculate_elevation_score(300) == 40.0


def test_elevation_1000_ft_returns_30():
    """2. Elevation 1000 ft returns 30."""
    assert calculate_elevation_score(1000) == 30.0


def test_elevation_2000_ft_returns_20():
    """3. Elevation 2000 ft returns 20."""
    assert calculate_elevation_score(2000) == 20.0


def test_elevation_4000_ft_returns_10():
    """4. Elevation 4000 ft returns 10."""
    assert calculate_elevation_score(4000) == 10.0


def test_elevation_6000_ft_returns_0():
    """5. Elevation 6000 ft returns 0."""
    assert calculate_elevation_score(6000) == 0.0


# --- 6 to 9: Temperature Tests ---

def test_temperature_20_c_returns_60():
    """6. Temperature 20°C returns 60."""
    assert calculate_temperature_score(20) == 60.0


def test_temperature_12_c_returns_45():
    """7. Temperature 12°C returns 45."""
    assert calculate_temperature_score(12) == 45.0


def test_temperature_7_c_returns_25():
    """8. Temperature 7°C returns 25."""
    assert calculate_temperature_score(7) == 25.0


def test_temperature_40_c_returns_10():
    """9. Temperature 40°C returns 10."""
    assert calculate_temperature_score(40) == 10.0


# --- 10 & 11: Unavailable Factors (Never 0) ---

def test_unavailable_elevation_returns_unavailable():
    """10. Unavailable elevation returns unavailable (None, never 0)."""
    result = calculate_elevation_score(None)
    assert result is None
    assert result != 0


def test_unavailable_temperature_returns_unavailable():
    """11. Unavailable temperature returns unavailable (None, never 0)."""
    result = calculate_temperature_score(None)
    assert result is None
    assert result != 0


# --- 12: Both Factors Available ---

def test_total_score_both_factors_available():
    """12. Test total score when both factors are available."""
    # Elevation: 1000 ft (30 pts) + Temperature: 12°C (45 pts) = 75 pts
    elev_score = calculate_elevation_score(1000)
    temp_score = calculate_temperature_score(12)
    total = calculate_total_score(elev_score, temp_score)

    assert elev_score == 30.0
    assert temp_score == 45.0
    assert total == 75.0

    summary = compute_assessment_scoring(elevation=1000, temperature=12)
    assert summary["total_score"] == 75.0
    assert summary["max_available_points"] == 100.0
    assert summary["status"] == "complete"


# --- 13: One Factor Unavailable (Never treats missing as 0) ---

def test_total_score_elevation_available_temperature_unavailable():
    """13a. Total score when elevation is available (30 pts) and temperature is unavailable."""
    elev_score = calculate_elevation_score(1000)  # 30 pts
    temp_score = calculate_temperature_score(None)  # None

    total = calculate_total_score(elev_score, temp_score)
    # Total must be 30.0 (30 out of 40 available points), NOT (30 + 0)/2 or 0
    assert total == 30.0
    assert total != 0

    summary = compute_assessment_scoring(elevation=1000, temperature=None)
    assert summary["elevation_score"] == 30.0
    assert summary["temperature_score"] is None
    assert summary["total_score"] == 30.0
    assert summary["max_available_points"] == 40.0
    assert summary["status"] == "partial"


def test_total_score_elevation_unavailable_temperature_available():
    """13b. Total score when elevation is unavailable and temperature is available (45 pts)."""
    elev_score = calculate_elevation_score(None)  # None
    temp_score = calculate_temperature_score(12)  # 45 pts

    total = calculate_total_score(elev_score, temp_score)
    # Total must be 45.0 (45 out of 60 available points), NOT (0 + 45)/2 or 0
    assert total == 45.0
    assert total != 0

    summary = compute_assessment_scoring(elevation=None, temperature=12)
    assert summary["elevation_score"] is None
    assert summary["temperature_score"] == 45.0
    assert summary["total_score"] == 45.0
    assert summary["max_available_points"] == 60.0
    assert summary["status"] == "partial"


def test_total_score_both_unavailable():
    """Both factors unavailable returns None (never 0)."""
    elev_score = calculate_elevation_score(None)
    temp_score = calculate_temperature_score(None)
    total = calculate_total_score(elev_score, temp_score)

    assert total is None
    assert total != 0

    summary = compute_assessment_scoring(elevation=None, temperature=None)
    assert summary["total_score"] is None
    assert summary["max_available_points"] == 0.0
    assert summary["status"] == "failed"
