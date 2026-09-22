from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any

class Location(BaseModel):
    latitude: float
    longitude: float

class EventIn(BaseModel):
    event_id: str
    bus_id: str
    route_id: str | None = None
    event_type: str
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime
    location: Location
    bbox: dict | None = None
    object_class: str | None = None
    track_id: int | None = None
    evidence_path: str | None = None
    plate_text: str | None = None
    plate_hash: str | None = None
    privacy_processed: bool = False
    model_name: str | None = None
    model_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    record_hmac: str | None = None

class EventOut(EventIn):
    pass
