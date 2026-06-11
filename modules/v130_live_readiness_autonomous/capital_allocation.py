
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
from .common import init_db, connect, safe_float, V130_VERSION

DEFAULT_TARGETS = {
    "US_EQUITY": 45.0,
    "GOLD": 20.0,
    "CASH": 20.0,
    "CRYPTO": 5.0,
    "TACTICAL": 10.0,
}

def current_exposure() -> Dict[str, float]:
    raw = os.getenv("V130_CURRENT_EXPOSURE", os.getenv("V110_POSITIONS", "US_EQUITY:40,GOLD:15,CASH:30,CRYPTO:3,TACTICAL:12"))
    out: Dict[str, float] = {}
    for p in raw.split(","):
        if ":" in p:
            k, v = p.split(":", 1)
            out[k.strip().upper()] = safe_float(v, 0) or 0
    return out

def target_allocation() -> Dict[str, float]:
    raw = os.getenv("V130_TARGET_ALLOCATION", "")
    if not raw:
        return DEFAULT_TARGETS.copy()
    out = {}
    for p in raw.split(","):
        if ":" in p:
            k, v = p.split(":", 1)
            out[k.strip().upper()] = safe_float(v, 0) or 0
    return out or DEFAULT_TARGETS.copy()

def allocation_plan() -> Dict[str, Any]:
    init_db()
    targets = target_allocation()
    current = current_exposure()
    threshold = safe_float(os.getenv("V130_REBALANCE_THRESHOLD", "5"), 5) or 5
    items = []
    for bucket, target in targets.items():
        cur = current.get(bucket, 0)
        drift = round(cur - target, 2)
        if abs(drift) < threshold:
            action = "HOLD"
        elif drift > 0:
            action = "REDUCE"
        else:
            action = "ADD"
        items.append({"bucket": bucket, "target_weight": target, "current_weight": cur, "drift": drift, "action": action})
    try:
        conn = connect()
        cur = conn.cursor()
        for i in items:
            cur.execute("INSERT OR REPLACE INTO v130_capital_allocation(bucket,target_weight,current_weight,drift,action,updated_at) VALUES(?,?,?,?,?,?)",
                        (i["bucket"], i["target_weight"], i["current_weight"], i["drift"], i["action"], datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()
    except Exception:
        pass
    return {"ok": True, "version": V130_VERSION, "threshold_pct": threshold, "items": items, "decision": "REBALANCE_NEEDED" if any(i["action"] != "HOLD" for i in items) else "BALANCED"}
