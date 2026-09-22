from __future__ import annotations


def maintenance_priority(severity: float, traffic_exposure: float, recurrence: float,
                          safety_risk: float, weights: dict | None = None) -> dict:
    w = weights or {"severity":0.35,"traffic_exposure":0.25,"recurrence":0.20,"safety_risk":0.20}
    score = (severity*w["severity"] + traffic_exposure*w["traffic_exposure"] +
             recurrence*w["recurrence"] + safety_risk*w["safety_risk"])
    score = max(0.0, min(100.0, score))
    priority = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"
    return {"priority_score": round(score,2), "priority": priority}
