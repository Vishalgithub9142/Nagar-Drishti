from __future__ import annotations
import json
import math
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import EventModel, MaintenanceModel
from edge.fusion import haversine_m
from edge.road_health import road_health_score
from edge.maintenance import maintenance_priority


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
