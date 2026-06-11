
from __future__ import annotations
from datetime import datetime, timezone
from .common import init_db, connect, V230_VERSION
from .portfolio_book import portfolio_snapshot

TARGETS = {"ETF": 35, "US_STOCK": 25, "GOLD": 15, "CRYPTO": 5, "CASH": 20, "OTHER": 0}

def rebalance_plan():
    init_db()
    snap = portfolio_snapshot()
    exposure = snap.get("exposure", {})
    items = []
    for bucket, target in TARGETS.items():
        cur = exposure.get(bucket, 0)
        drift = round(cur - target, 2)
        if abs(drift) < 5:
            action = "HOLD"
        elif drift > 0:
            action = "REDUCE"
        else:
            action = "ADD"
        items.append({"bucket": bucket, "current_weight": cur, "target_weight": target, "drift": drift, "action": action})
    try:
        conn = connect(); cur = conn.cursor()
        for i in items:
            if i["action"] != "HOLD":
                cur.execute("INSERT INTO v230_rebalance_queue(created_at,symbol,action,current_weight,target_weight,drift,status,reason,model_version) VALUES(?,?,?,?,?,?,?,?,?)",
                            (datetime.now(timezone.utc).isoformat(), i["bucket"], i["action"], i["current_weight"], i["target_weight"], i["drift"], "PENDING_REVIEW", "portfolio_drift", V230_VERSION))
        conn.commit(); conn.close()
    except Exception:
        pass
    return {"ok": True, "decision": "REBALANCE_NEEDED" if any(i["action"]!="HOLD" for i in items) else "BALANCED", "items": items}
