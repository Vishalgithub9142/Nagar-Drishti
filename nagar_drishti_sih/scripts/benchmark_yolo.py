from __future__ import annotations
import argparse
from ultralytics import YOLO


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--weights', required=True)
    ap.add_argument('--data', required=True, help='YOLO data.yaml')
    args=ap.parse_args()
    model=YOLO(args.weights)
    metrics=model.val(data=args.data, verbose=True)
    print('\n=== MEASURED MODEL RESULTS ===')
    print('mAP50:', float(metrics.box.map50))
    print('mAP50-95:', float(metrics.box.map))
    if hasattr(metrics.box, 'mp'):
        print('precision:', float(metrics.box.mp))
    if hasattr(metrics.box, 'mr'):
        print('recall:', float(metrics.box.mr))

if __name__=='__main__': main()
