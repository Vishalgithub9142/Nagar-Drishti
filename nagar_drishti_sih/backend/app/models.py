from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class EventModel(Base):
    __tablename__ = 'events'
    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    bus_id: Mapped[str] = mapped_column(String(64), index=True)
    route_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    object_class: Mapped[str | None] = mapped_column(String(128), nullable=True)
    track_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    plate_text: Mapped[str | None] = mapped_column(String(32), nullable=True)
    plate_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    privacy_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default='{}')
    record_hmac: Mapped[str | None] = mapped_column(String(128), nullable=True)

class AssetModel(Base):
    __tablename__ = 'expected_assets'
    asset_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_type: Mapped[str] = mapped_column(String(64), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    route_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

class MaintenanceModel(Base):
    __tablename__ = 'maintenance_items'
    item_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    road_key: Mapped[str] = mapped_column(String(128), index=True)
    priority_score: Mapped[float] = mapped_column(Float)
    priority: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(32), default='OPEN')
    reason_json: Mapped[str] = mapped_column(Text, default='{}')
