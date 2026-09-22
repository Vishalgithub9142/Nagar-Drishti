from __future__ import annotations
from pathlib import Path
import os
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_config(path: str | Path | None = None) -> dict:
    cfg_path = Path(path) if path else ROOT / "config" / "config.yaml"
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg.setdefault("security", {})
    cfg["security"]["hmac_key"] = os.getenv("NAGAR_HMAC_KEY", cfg["security"].get("hmac_key", "CHANGE_ME"))
    return cfg
