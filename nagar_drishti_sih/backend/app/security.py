from __future__ import annotations
import hashlib
import hmac
import json
import os


def canonical_event_dict(payload: dict) -> dict:
    out = dict(payload)
    out.pop('record_hmac', None)
    return out


def make_hmac(payload: dict) -> str:
    key = os.getenv('NAGAR_HMAC_KEY', 'CHANGE_ME')
    raw = json.dumps(canonical_event_dict(payload), sort_keys=True, separators=(',', ':')).encode()
    return hmac.new(key.encode(), raw, hashlib.sha256).hexdigest()


def verify_hmac(payload: dict) -> bool:
    provided = payload.get('record_hmac')
    if not provided:
        return False
    return hmac.compare_digest(provided, make_hmac(payload))
