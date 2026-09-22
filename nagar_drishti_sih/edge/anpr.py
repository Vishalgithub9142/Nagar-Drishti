from __future__ import annotations
from pathlib import Path
import hashlib
import re
import cv2

try:
    from paddleocr import PaddleOCR
except Exception:
    PaddleOCR = None


class ANPR:
    def __init__(self, plate_model_path: str, conf: float = 0.35):
        from ultralytics import YOLO
        self.model = YOLO(plate_model_path)
        self.conf = conf
        self.ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False,
                             use_textline_orientation=False, lang='en') if PaddleOCR else None

    def detect_and_read(self, frame):
        if self.ocr is None:
            return []
        results = self.model.predict(frame, conf=self.conf, verbose=False)
        out = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes.xyxy.cpu().numpy().tolist():
                x1,y1,x2,y2 = [int(v) for v in box]
                crop = frame[max(0,y1):max(y1+1,y2), max(0,x1):max(x1+1,x2)]
                if crop.size == 0:
                    continue
                ocr_res = self.ocr.predict(crop)
                texts = []
                for page in ocr_res:
                    data = page.json if hasattr(page, 'json') else None
                    if data:
                        texts.extend(re.findall(r"[A-Z0-9-]{4,}", str(data).upper()))
                if texts:
                    plate = max(texts, key=len)
                    plate = re.sub(r"[^A-Z0-9]", "", plate)
                    out.append({
                        "plate_text": plate,
                        "plate_hash": hashlib.sha256(plate.encode()).hexdigest(),
                        "bbox": [x1,y1,x2,y2]
                    })
        return out
