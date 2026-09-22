"""
NAGAR DRISHTI - Frame Router & Multi-Model Pipeline Architecture
----------------------------------------------------------------
Defensible SIH Architecture:
Divides the vision pipeline into 3 task-specific model heads:
  1. Road Model    : Defect detection (Potholes, Cracks, Waterlogging)
  2. Traffic Model : Vehicle detection + ByteTrack + ANPR OCR
  3. Safety Model  : Infrastructure assets (Markings, Pedestrians, Signs)
"""

import os
import json
import time

class FrameRouter:
    """Dispatches camera feed frames to task-specific inference heads."""
    def __init__(self, road_model, traffic_model, safety_model):
        self.road_model = road_model
        self.traffic_model = traffic_model
        self.safety_model = safety_model

    def process_frame(self, frame_data):
        timestamp = frame_data.get("timestamp", time.time())
        frame_id = frame_data.get("frame_id", 0)

        # 1. Dispatch to Road Defect Model
        road_results = self.road_model.infer(frame_data)

        # 2. Dispatch to Traffic & Tracking Model
        traffic_results = self.traffic_model.infer(frame_data)

        # 3. Dispatch to Safety & Infrastructure Asset Model
        safety_results = self.safety_model.infer(frame_data)

        return {
            "frame_id": frame_id,
            "timestamp": timestamp,
            "road_defects": road_results,
            "traffic_analytics": traffic_results,
            "safety_infrastructure": safety_results
        }

class RoadDefectModel:
    """Specialized head for road surface anomalies."""
    def __init__(self, weights_path="weights/best.pt"):
        self.classes = {0: "Pothole", 1: "Road Crack", 2: "Waterlogging"}
        self.weights = weights_path

    def infer(self, frame_data):
        # Simulated inference on road surface head
        return [
            {"class_id": 0, "class_name": "Pothole", "confidence": 0.912, "bbox": [120, 340, 280, 490]}
        ]

class TrafficTrackingModel:
    """Specialized head for vehicle tracking (ByteTrack) + ANPR."""
    def __init__(self, weights_path="yolov8n.pt"):
        self.classes = {0: "Car", 1: "Bus", 2: "Truck", 3: "Motorcycle", 4: "License Plate"}
        self.weights = weights_path

    def infer(self, frame_data):
        return {
            "vehicles_tracked": [
                {"track_id": 1, "class_name": "Bus", "confidence": 0.94, "bbox": [50, 100, 300, 400]},
                {"track_id": 2, "class_name": "Car", "confidence": 0.89, "bbox": [420, 200, 580, 350]}
            ],
            "anpr_detected": [
                {"track_id": 2, "plate_text": "MH14EH7958", "ocr_confidence": 0.958}
            ]
        }

class SafetyInfrastructureModel:
    """Specialized head for road markings, signs, and asset comparisons."""
    def __init__(self):
        self.classes = {0: "Pedestrian", 1: "Road Marking / Zebra Crossing", 2: "Traffic Sign"}

    def infer(self, frame_data):
        return {
            "assets_detected": [
                {"class_name": "Road Marking / Zebra Crossing", "confidence": 0.88, "condition": "Faded / Worn"}
            ],
            "asset_absence_analysis": "Detected faded road marking; asset condition flagged for municipal review via repeated spatial verification."
        }

def run_multi_model_pipeline_demo():
    print("=" * 70)
    print("   NAGAR DRISHTI - MULTI-MODEL MODULAR PIPELINE EXECUTION   ")
    print("=" * 70)

    road_head = RoadDefectModel()
    traffic_head = TrafficTrackingModel()
    safety_head = SafetyInfrastructureModel()

    router = FrameRouter(road_head, traffic_head, safety_head)

    sample_frame = {"frame_id": 101, "timestamp": time.time()}
    output = router.process_frame(sample_frame)

    print("\n[FRAME ROUTER DISPATCH SUCCESSFUL]")
    print(json.dumps(output, indent=4))
    print("=" * 70)

if __name__ == "__main__":
    run_multi_model_pipeline_demo()
