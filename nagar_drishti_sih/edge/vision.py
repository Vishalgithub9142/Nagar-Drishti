from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import cv2
from ultralytics import YOLO


class VisionEngine:
    def __init__(self, road_model: str, vehicle_model: str, conf=0.35, imgsz=640, tracker="bytetrack.yaml"):
        self.road = YOLO(road_model)
        self.vehicle = YOLO(vehicle_model)
        self.conf = conf
        self.imgsz = imgsz
        self.tracker_cfg = tracker

    def road_events(self, frame):
        results = self.road.predict(frame, conf=self.conf, imgsz=self.imgsz, verbose=False)
        events = []
        for r in results:
            names = r.names
            if r.boxes is None:
                continue
            for box in r.boxes:
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                cls = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                events.append({
                    "class_name": str(names.get(cls, cls)),
                    "confidence": conf,
                    "bbox": xyxy,
                })
        return events

    def track_vehicles(self, frame):
        results = self.vehicle.track(frame, conf=self.conf, imgsz=self.imgsz,
                                     tracker=self.tracker_cfg, persist=True, verbose=False)
        tracked = []
        for r in results:
            if r.boxes is None:
                continue
            ids = r.boxes.id.cpu().numpy().tolist() if r.boxes.id is not None else [None]*len(r.boxes)
            for box, tid in zip(r.boxes, ids):
                cls = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                tracked.append({
                    "class_id": cls,
                    "confidence": conf,
                    "track_id": int(tid) if tid is not None else None,
                    "bbox": xyxy,
                })
        return tracked
