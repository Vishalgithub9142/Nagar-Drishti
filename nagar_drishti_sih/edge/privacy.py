from __future__ import annotations
import cv2
from pathlib import Path


def blur_faces(frame, min_size=(40, 40)):
    """Prototype privacy transform. For production, validate a modern face detector on local data."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=min_size)
    out = frame.copy()
    for (x, y, w, h) in faces:
        roi = out[y:y+h, x:x+w]
        if roi.size:
            out[y:y+h, x:x+w] = cv2.GaussianBlur(roi, (31, 31), 0)
    return out, len(faces)


def save_privacy_processed(frame, path: str) -> tuple[str, int]:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    processed, count = blur_faces(frame)
    cv2.imwrite(path, processed)
    return path, count
