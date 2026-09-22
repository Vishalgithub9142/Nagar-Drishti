from __future__ import annotations
from datetime import datetime, timezone
import os
from pathlib import Path
import hashlib
import hmac
import json
import cv2
from .schemas import Event, GeoPoint, BoundingBox
from .db import EdgeQueue
from .privacy import save_privacy_processed


def record_hmac(payload: dict, key: str) -> str:
    clean = dict(payload)
    clean.pop("record_hmac", None)
    raw = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(key.encode(), raw, hashlib.sha256).hexdigest()


def build_event(bus_id: str, route_id: str | None, event_type: str, confidence: float,
                location: dict, bbox: list | None = None, **kwargs) -> Event:
    event = Event(
        bus_id=bus_id,
        route_id=route_id,
        event_type=event_type,
        confidence=float(confidence),
        location=GeoPoint(**location),
        bbox=BoundingBox(x1=bbox[0], y1=bbox[1], x2=bbox[2], y2=bbox[3]) if bbox else None,
        **kwargs,
    )
    return event


def persist_event(queue: EdgeQueue, event: Event, evidence_frame=None, evidence_path: str | None = None, hmac_key: str | None = None):
    if evidence_frame is not None and evidence_path:
        saved, count = save_privacy_processed(evidence_frame, evidence_path)
        event.evidence_path = saved
        event.privacy_processed = True
        event.metadata["faces_blurred"] = count
    key = hmac_key or os.getenv("NAGAR_HMAC_KEY")
    if key:
        event.record_hmac = record_hmac(event.model_dump(mode="json"), key)
    queue.put(event)
    return event
