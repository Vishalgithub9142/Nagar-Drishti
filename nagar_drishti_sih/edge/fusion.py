from __future__ import annotations
from datetime import timedelta
from math import radians, sin, cos, sqrt, atan2
from sklearn.cluster import DBSCAN
import numpy as np


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = radians(lat1), radians(lat2)
    dlat = radians(lat2-lat1)
    dlon = radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(p1)*cos(p2)*sin(dlon/2)**2
    return 2*r*atan2(sqrt(a), sqrt(1-a))


def fuse_events(events: list[dict], radius_m: float = 25, time_window_s: int = 900) -> list[dict]:
    """Cluster same-type events by geo proximity and time. Returns master defects."""
    if not events:
        return []
    groups = []
    by_type = {}
    for e in events:
        by_type.setdefault(e.get("event_type"), []).append(e)
    for event_type, items in by_type.items():
        if len(items) == 1:
            groups.append(items)
            continue
        coords = np.array([[e["location"]["latitude"], e["location"]["longitude"]] for e in items])
        scale = 1 / 111_000.0
        eps = radius_m * scale
        labels = DBSCAN(eps=eps, min_samples=1, metric="euclidean").fit(coords).labels_
        for label in sorted(set(labels)):
            cluster = [e for e, lab in zip(items, labels) if lab == label]
            cluster.sort(key=lambda x: x.get("timestamp", ""))
            kept = []
            for e in cluster:
                if not kept:
                    kept.append(e); continue
                from dateutil.parser import isoparse
                t1 = isoparse(kept[-1]["timestamp"])
                t2 = isoparse(e["timestamp"])
                if abs((t2-t1).total_seconds()) <= time_window_s:
                    kept.append(e)
                else:
                    groups.append(kept); kept = [e]
            if kept: groups.append(kept)

    masters = []
    for cluster in groups:
        lats = [e["location"]["latitude"] for e in cluster]
        lons = [e["location"]["longitude"] for e in cluster]
        conf = sum(float(e.get("confidence",0)) for e in cluster) / len(cluster)
        masters.append({
            "event_type": cluster[0]["event_type"],
            "location": {"latitude": sum(lats)/len(lats), "longitude": sum(lons)/len(lons)},
            "observation_count": len(cluster),
            "bus_ids": sorted(set(e["bus_id"] for e in cluster)),
            "confidence": round(conf, 4),
            "event_ids": [e["event_id"] for e in cluster],
        })
    return masters
