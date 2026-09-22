from __future__ import annotations
import time
import requests
from .db import EdgeQueue


def sync_once(queue: EdgeQueue, backend_url: str, batch_size: int = 25, timeout: int = 10):
    events = queue.pending(batch_size)
    if not events:
        return {"sent": 0, "failed": 0}
    sent = failed = 0
    for event in events:
        try:
            r = requests.post(f"{backend_url.rstrip('/')}/api/events", json=event.model_dump(mode="json"), timeout=timeout)
            if r.ok:
                queue.ack(event.event_id)
                sent += 1
            else:
                queue.fail(event.event_id, r.text, time.time()+10)
                failed += 1
        except requests.RequestException as exc:
            queue.fail(event.event_id, str(exc), time.time()+30)
            failed += 1
    return {"sent": sent, "failed": failed}
