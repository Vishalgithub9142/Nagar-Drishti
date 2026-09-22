from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models import EventModel, AssetModel
from .schemas import EventIn
from .services import recent_events, metrics, road_health, build_maintenance_queue, event_to_dict
from .security import make_hmac, verify_hmac

Base.metadata.create_all(bind=engine)
app = FastAPI(title='Nagar Drishti API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

@app.get('/api/health')
def health():
    return {'status':'ok','service':'nagar-drishti-api','time':datetime.now(timezone.utc)}

@app.post('/api/events')
def create_event(payload: EventIn, db: Session = Depends(get_db)):
    existing = db.get(EventModel, payload.event_id)
    if existing:
        return {'status':'already_exists','event_id':payload.event_id}
    body = payload.model_dump(mode='json')
    if body.get('record_hmac') and os.getenv('NAGAR_HMAC_KEY'):
        if not verify_hmac(body):
            raise HTTPException(status_code=400, detail='Invalid event HMAC')
    e = EventModel(
        event_id=payload.event_id, bus_id=payload.bus_id, route_id=payload.route_id,
        event_type=payload.event_type, confidence=payload.confidence, timestamp=payload.timestamp,
        latitude=payload.location.latitude, longitude=payload.location.longitude,
        object_class=payload.object_class, track_id=payload.track_id,
        evidence_path=payload.evidence_path, plate_text=(payload.plate_text if os.getenv('STORE_PLAINTEXT_PLATE','false').lower()=='true' else None),
        plate_hash=payload.plate_hash, privacy_processed=payload.privacy_processed,
        model_name=payload.model_name, model_version=payload.model_version,
        metadata_json=json.dumps(payload.metadata), record_hmac=payload.record_hmac,
    )
    db.add(e); db.commit()
    return {'status':'created','event_id':e.event_id}

@app.get('/api/events')
def get_events(limit:int=Query(200,ge=1,le=2000), event_type:str|None=None, db:Session=Depends(get_db)):
    q=select(EventModel).order_by(EventModel.timestamp.desc()).limit(limit)
    if event_type: q=select(EventModel).where(EventModel.event_type==event_type).order_by(EventModel.timestamp.desc()).limit(limit)
    return [event_to_dict(e) for e in db.execute(q).scalars().all()]

@app.get('/api/metrics')
def get_metrics(db:Session=Depends(get_db)): return metrics(db)

@app.get('/api/road-health')
def get_road_health(db:Session=Depends(get_db)): return road_health(db)

@app.get('/api/maintenance')
def get_maintenance(db:Session=Depends(get_db)): return build_maintenance_queue(db)

@app.get('/api/gis/geojson')
def geojson(limit:int=500, db:Session=Depends(get_db)):
    events=recent_events(db,limit)
    features=[]
    for e in events:
        features.append({'type':'Feature','geometry':{'type':'Point','coordinates':[e['location']['longitude'],e['location']['latitude']]},'properties':e})
    return {'type':'FeatureCollection','features':features}

@app.post('/api/demo/clear')
def clear_demo(db:Session=Depends(get_db)):
    # Prototype-only helper.
    db.query(EventModel).delete(); db.commit(); return {'status':'cleared'}
