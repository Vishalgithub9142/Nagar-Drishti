from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path
import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from edge.config import load_config
from edge.db import EdgeQueue
from edge.vision import VisionEngine
from edge.event_pipeline import build_event, persist_event
from edge.risk import UnsafeDrivingDetector
from edge.anpr import ANPR
from edge.sync_client import sync_once


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, help='Camera index such as 0, or a video path')
    ap.add_argument('--bus-id', required=True)
    ap.add_argument('--config', default='config/config.yaml')
    ap.add_argument('--lat', type=float, default=26.123456)
    ap.add_argument('--lon', type=float, default=85.123456)
    args = ap.parse_args()
    cfg = load_config(args.config)

    source = int(args.source) if args.source.isdigit() else args.source
    if isinstance(source, int):
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(source)
    else:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        raise SystemExit(f'Unable to open source: {args.source}')

    vision = VisionEngine(
        cfg['models']['road_model'],
        cfg['models']['vehicle_model'],
        conf=cfg['inference']['conf'],
        imgsz=cfg['inference']['imgsz'],
        tracker=cfg['models']['tracker'],
    )
    queue = EdgeQueue(cfg['storage']['edge_db'])
    risk_engine = UnsafeDrivingDetector()
    plate_reader = None
    plate_path = Path(cfg['models']['plate_model'])
    if plate_path.exists():
        try:
            plate_reader = ANPR(str(plate_path), conf=cfg['inference']['conf'])
        except Exception as exc:
            print(f'ANPR disabled: {exc}')
    evidence_dir = Path(cfg['storage']['evidence_dir'])
    evidence_dir.mkdir(parents=True, exist_ok=True)

    route_id = cfg['bus'].get('route_id')
    frame_no = 0
    last_sync = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            if not isinstance(source, int):
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = cap.read()
                if not ok:
                    break
            else:
                break
        frame_no += 1

        roads = vision.road_events(frame)
        for idx, item in enumerate(roads):
            cls = item['class_name'].lower()
            event_type = cls.replace(' ', '_')
            if event_type not in {'pothole','crack','waterlogging','incident','pedestrian_risk','infrastructure_observation'}:
                event_type = 'infrastructure_observation'
            event = build_event(
                bus_id=args.bus_id,
                route_id=route_id,
                event_type=event_type,
                confidence=item['confidence'],
                location={'latitude': args.lat, 'longitude': args.lon},
                bbox=item['bbox'],
                object_class=item['class_name'],
                model_name='road_model',
                metadata={'frame_no': frame_no},
            )
            ev_path = evidence_dir / f"{event.event_id}.jpg"
            persist_event(queue, event, evidence_frame=frame, evidence_path=str(ev_path), hmac_key=cfg['security'].get('hmac_key'))

        vehicles = vision.track_vehicles(frame)
        if vehicles:
            # One aggregate traffic event per frame rather than one event per vehicle.
            event = build_event(
                bus_id=args.bus_id,
                route_id=route_id,
                event_type='vehicle',
                confidence=sum(v['confidence'] for v in vehicles)/len(vehicles),
                location={'latitude': args.lat, 'longitude': args.lon},
                model_name='vehicle_model',
                metadata={'frame_no':frame_no,'vehicle_count':len(vehicles), 'tracks':[v['track_id'] for v in vehicles if v['track_id'] is not None]},
            )
            persist_event(queue, event, hmac_key=cfg['security'].get('hmac_key'))

            # Prototype unsafe-driving screening from image-plane trajectory changes.
            for v in vehicles:
                if v['track_id'] is None:
                    continue
                x1,y1,x2,y2 = v['bbox']
                risk = risk_engine.update(v['track_id'], (x1+x2)/2, (y1+y2)/2, time.monotonic())
                if risk:
                    risk_event = build_event(
                        bus_id=args.bus_id, route_id=route_id, event_type='unsafe_driving',
                        confidence=risk['risk'], location={'latitude':args.lat,'longitude':args.lon},
                        track_id=v['track_id'], object_class='vehicle', model_name='trajectory_heuristic',
                        metadata={'reasons':risk['reasons'],'frame_no':frame_no}
                    )
                    persist_event(queue, risk_event, hmac_key=cfg['security'].get('hmac_key'))

        if plate_reader is not None and frame_no % 5 == 0:
            try:
                plates = plate_reader.detect_and_read(frame)
                for plate in plates:
                    meta = dict(plate)
                    plate_text = plate['plate_text'] if cfg['privacy'].get('store_plaintext_plate', False) else None
                    plate_event = build_event(
                        bus_id=args.bus_id, route_id=route_id, event_type='anpr', confidence=0.8,
                        location={'latitude':args.lat,'longitude':args.lon}, model_name='plate_model+paddleocr',
                        plate_text=plate_text, plate_hash=plate['plate_hash'], metadata=meta
                    )
                    persist_event(queue, plate_event, evidence_frame=frame,
                                  evidence_path=str(evidence_dir / f'{plate_event.event_id}.jpg'),
                                  hmac_key=cfg['security'].get('hmac_key'))
            except Exception as exc:
                print(f'ANPR frame skipped: {exc}')

        now = time.time()
        if now-last_sync >= 2:
            sync_once(queue, cfg['sync']['backend_url'], cfg['sync']['batch_size'], cfg['sync']['timeout_seconds'])
            last_sync = now

        cv2.putText(frame, f"Bus {args.bus_id} | frame {frame_no}", (20,40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
        cv2.imshow('Nagar Drishti Edge', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release(); cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
