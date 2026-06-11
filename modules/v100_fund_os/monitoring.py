
from __future__ import annotations
from typing import Dict, Any
from .database import init_db, last_audit
from .config import config_status, V100_VERSION
from .broker import broker_status

def health() -> Dict[str, Any]:
    db = init_db()
    cfg = config_status()
    broker = broker_status()
    return {"ok": bool(db.get("ok")), "version": V100_VERSION, "db": db, "config": cfg, "broker": broker, "last_audit": last_audit(5)}
