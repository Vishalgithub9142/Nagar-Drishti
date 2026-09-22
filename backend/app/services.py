from __future__ import annotations
import json
import math
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import EventModel, MaintenanceModel

def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2)**2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def road_health_score(defect_events: list[dict], water_events: int = 0, incident_events: int = 0, traffic_exposure: float = 0.0) -> dict:
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

def maintenance_priority(severity: float, traffic_exposure: float, recurrence: float, safety_risk: float, weights: dict | None = None) -> dict:
    w = weights or {"severity": 0.35, "traffic_exposure": 0.25, "recurrence": 0.20, "safety_risk": 0.20}
    score = (severity * w["severity"] + traffic_exposure * w["traffic_exposure"] + recurrence * w["recurrence"] + safety_risk * w["safety_risk"])
    score = max(0.0, min(100.0, score))
    priority = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"
    return {"priority_score": round(score, 2), "priority": priority}


def event_to_dict(e: EventModel):
    return {
        'event_id':e.event_id,'bus_id':e.bus_id,'route_id':e.route_id,'event_type':e.event_type,
        'confidence':e.confidence,'timestamp':e.timestamp.isoformat(),'location':{'latitude':e.latitude,'longitude':e.longitude},
        'object_class':e.object_class,'track_id':e.track_id,'evidence_path':e.evidence_path,
        'plate_hash':e.plate_hash,'privacy_processed':e.privacy_processed,'model_name':e.model_name,
        'model_version':e.model_version,'metadata':json.loads(e.metadata_json or '{}'), 'record_hmac':e.record_hmac
    }


def recent_events(db: Session, limit=200):
    rows = db.execute(select(EventModel).order_by(EventModel.timestamp.desc()).limit(limit)).scalars().all()
    return [event_to_dict(e) for e in rows]


def metrics(db: Session):
    events = db.execute(select(EventModel)).scalars().all()
    by = defaultdict(int)
    for e in events: by[e.event_type] += 1
    return {'total_events':len(events), 'by_type':dict(by), 'active_buses':len(set(e.bus_id for e in events))}


def road_health(db: Session):
    groups = defaultdict(list)
    for e in db.execute(select(EventModel)).scalars().all():
        key = f'{round(e.latitude,4)},{round(e.longitude,4)}'
        groups[key].append(e)
    out=[]
    for key, evs in groups.items():
        defect = [event_to_dict(e) for e in evs if e.event_type in {'pothole','crack','waterlogging','incident'}]
        score = road_health_score(defect,
                                  water_events=sum(e.event_type=='waterlogging' for e in evs),
                                  incident_events=sum(e.event_type=='incident' for e in evs),
                                  traffic_exposure=min(1.0, sum(e.event_type=='vehicle' for e in evs)/50))
        out.append({'road_key':key, **score, 'event_count':len(evs), 'last_seen':max(e.timestamp for e in evs).isoformat()})
    return sorted(out, key=lambda x:x['score'])


def build_maintenance_queue(db: Session):
    roads = road_health(db)
    result=[]
    for r in roads:
        severity = max(0,100-r['score'])
        traffic = min(100, r['event_count']*5)
        recurrence = min(100, r['recurrence']*10)
        safety = 80 if r['score'] < 40 else 50 if r['score'] < 70 else 20
        pri = maintenance_priority(severity,traffic,recurrence,safety)
        result.append({**r,**pri})
    return sorted(result,key=lambda x:x['priority_score'],reverse=True)
