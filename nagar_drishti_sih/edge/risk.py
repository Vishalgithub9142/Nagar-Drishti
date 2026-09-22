from __future__ import annotations
from dataclasses import dataclass
from math import hypot


@dataclass
class TrackPoint:
    x: float
    y: float
    t: float


class UnsafeDrivingDetector:
    """Camera-geometry-independent heuristic for prototype screening.
    It estimates image-plane motion. Do not present this as legal speed/rash-driving determination.
    """
    def __init__(self, lane_change_px=120.0, sudden_delta_ratio=0.55):
        self.lane_change_px = lane_change_px
        self.sudden_delta_ratio = sudden_delta_ratio
        self.history: dict[int, list[TrackPoint]] = {}

    def update(self, track_id: int, center_x: float, center_y: float, timestamp_s: float):
        hist = self.history.setdefault(track_id, [])
        hist.append(TrackPoint(center_x, center_y, timestamp_s))
        if len(hist) > 8:
            del hist[:-8]
        if len(hist) < 4:
            return None
        velocities = []
        for a, b in zip(hist[:-1], hist[1:]):
            dt = max(b.t-a.t, 1e-3)
            velocities.append(hypot(b.x-a.x, b.y-a.y) / dt)
        recent = velocities[-1]
        median_prev = sorted(velocities[:-1])[len(velocities[:-1])//2]
        lane_shift = abs(hist[-1].x - hist[-4].x)
        sudden = median_prev > 1e-6 and abs(recent-median_prev)/median_prev >= self.sudden_delta_ratio
        lane_change = lane_shift >= self.lane_change_px
        if sudden or lane_change:
            reasons = []
            if sudden: reasons.append("sudden_image_plane_speed_change")
            if lane_change: reasons.append("large_lateral_motion")
            risk = min(1.0, 0.5 * float(sudden) + 0.5 * float(lane_change))
            return {"risk": risk, "reasons": reasons}
        return None
