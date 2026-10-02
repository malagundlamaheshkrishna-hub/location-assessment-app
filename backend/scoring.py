"""
Scoring engine for the Location Assessment Tool.

All scoring rules, point brackets, and composite score calculations
are contained within this single file.
"""

from typing import Optional, Dict, Any, Tuple

# Maximum point allocations per category
MAX_ELEVATION_POINTS = 40.0
MAX_TEMPERATURE_POINTS = 60.0
MAX_TOTAL_POINTS = MAX_ELEVATION_POINTS + MAX_TEMPERATURE_POINTS  # 100.0


def calculate_elevation_score(elevation: Optional[float]) -> Optional[float]:
    """
    Calculates the elevation score (maximum 40 points).

    Rules:
        0 - 500 ft:       40 points
        501 - 1500 ft:    30 points
        1501 - 3000 ft:   20 points
        3001 - 5000 ft:   10 points
        Above 5000 ft:     0 points

    Returns:
        float score (0.0 to 40.0) if elevation is available, None if unavailable.
        Does NOT convert unavailable elevation to 0.
    """
    if elevation is None:
        return None

    elev = float(elevation)

    if elev <= 500.0:
        return 40.0
    elif elev <= 1500.0:
        return 30.0
    elif elev <= 3000.0:
        return 20.0
    elif elev <= 5000.0:
        return 10.0
    else:
        return 0.0


def calculate_temperature_score(temperature: Optional[float]) -> Optional[float]:
    """
    Calculates the temperature score (maximum 60 points).

    Rules:
        15 - 25 °C:                      60 points
        10 - 14 °C or 26 - 30 °C:        45 points
        5 - 9 °C or 31 - 35 °C:          25 points
        Below 5 °C or above 35 °C:       10 points

    Returns:
        float score (10.0 to 60.0) if temperature is available, None if unavailable.
        Does NOT convert unavailable temperature to 0.
    """
    if temperature is None:
        return None

    temp = float(temperature)

    if 15.0 <= temp <= 25.0:
        return 60.0
    elif (10.0 <= temp < 15.0) or (25.0 < temp <= 30.0):
        return 45.0
    elif (5.0 <= temp < 10.0) or (30.0 < temp <= 35.0):
        return 25.0
    else:  # temp < 5.0 or temp > 35.0
        return 10.0


def calculate_total_score(
    elevation_score: Optional[float],
    temperature_score: Optional[float]
) -> Optional[float]:
    """
    Calculates the total score from available factors only.

    Important:
        - If both factors are available: sum of both scores (e.g. 30 + 45 = 75).
        - If only one factor is available: that factor's score alone (e.g. 30/40 available).
        - If neither factor is available: returns None.
        - NEVER treats a missing factor as 0.
    """
    available_scores = [s for s in (elevation_score, temperature_score) if s is not None]

    if not available_scores:
        return None

    return round(float(sum(available_scores)), 2)


def compute_assessment_scoring(
    elevation: Optional[float],
    temperature: Optional[float]
) -> Dict[str, Any]:
    """
    Evaluates all factors and returns a comprehensive score summary.

    Returns:
        Dictionary containing:
        - elevation_score: Optional[float]
        - temperature_score: Optional[float]
        - total_score: Optional[float]
        - max_available_points: float
        - status: str ('complete', 'partial', 'failed')
    """
    elev_score = calculate_elevation_score(elevation)
    temp_score = calculate_temperature_score(temperature)
    total = calculate_total_score(elev_score, temp_score)

    max_points = 0.0
    if elev_score is not None:
        max_points += MAX_ELEVATION_POINTS
    if temp_score is not None:
        max_points += MAX_TEMPERATURE_POINTS

    if elev_score is not None and temp_score is not None:
        status = "complete"
    elif elev_score is not None or temp_score is not None:
        status = "partial"
    else:
        status = "failed"

    return {
        "elevation_score": elev_score,
        "temperature_score": temp_score,
        "total_score": total,
        "max_available_points": max_points,
        "status": status
    }


def compute_total_score_and_status(
    elevation_score: Optional[float],
    temperature_score: Optional[float]
) -> Tuple[Optional[float], str]:
    """
    Backward-compatibility helper for calculating total score and status.
    """
    total = calculate_total_score(elevation_score, temperature_score)
    if elevation_score is not None and temperature_score is not None:
        status = "complete"
    elif elevation_score is not None or temperature_score is not None:
        status = "partial"
    else:
        status = "failed"
    return total, status
