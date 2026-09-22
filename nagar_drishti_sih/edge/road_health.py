from __future__ import annotations
from statistics import mean


def road_health_score(defect_events: list[dict], water_events: int = 0, incident_events: int = 0,
                      traffic_exposure: float = 0.0) -> dict:
    """0-100 health score: 100 is healthiest. Tunable, transparent rule-based prototype."""
    severity_map = {"pothole": 20, "crack": 12, "waterlogging": 18, "incident": 25}
    penalties = 0.0
    recurrence = len(defect_events)
    for e in defect_events:
        penalties += severity_map.get(e.get("event_type"), 5) * float(e.get("confidence", 0.5))
    penalties += min(20, water_events * 5)
    penalties += min(20, incident_events * 5)
    penalties += min(10, traffic_exposure * 10)
    score = max(0.0, min(100.0, 100.0 - penalties))
    return {
        "score": round(score, 1),
        "recurrence": recurrence,
        "defect_penalty": round(penalties, 2),
        "grade": "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D" if score >= 30 else "E",
    }
