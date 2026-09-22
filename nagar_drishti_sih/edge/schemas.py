from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Literal
import uuid

EventType = Literal[
    "pothole", "crack", "waterlogging", "vehicle", "traffic_congestion",
    "pedestrian_risk", "unsafe_driving", "anpr", "infrastructure_observation",
    "potential_missing_infrastructure", "incident"
]


class GeoPoint(BaseModel):
    latitude: float
    longitude: float


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Event(BaseModel):
    model_config = ConfigDict(extra="allow")
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bus_id: str
    route_id: str | None = None
    event_type: EventType
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    location: GeoPoint
    bbox: BoundingBox | None = None
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
