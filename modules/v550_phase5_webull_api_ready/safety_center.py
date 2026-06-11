
from __future__ import annotations
from datetime import datetime, timezone
import json
from .common import init_db, connect, V550_VERSION
from .api_health_center import api_health_center

def emergency_kill_switch(active=False, reason="manual_check"):
    init_db()
    status = "ACTIVE" if active else "READY"
    action = "BLOCK_ALL_ORDERS" if active else "NO_ACTION"
    report = {"active": active, "reason": reason, "action": action}
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v550_safety_events(created_at,event_type,severity,action,status,report,model_version) VALUES(?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), "KILL_SWITCH", "CRITICAL" if active else "INFO", action, status, json.dumps(report, ensure_ascii=False), V550_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V550_VERSION, **report}

def duplicate_order_protection(symbol="SPY", side="BUY"):
    init_db()
    conn = connect(); conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM v550_order_dryrun WHERE symbol=? AND side=? ORDER BY created_at DESC LIMIT 1", (symbol.upper(), side.upper()))
    row = cur.fetchone()
    conn.close()
    return {"ok": True, "duplicate_risk": bool(row), "last_order": dict(row) if row else None, "decision": "REVIEW_DUPLICATE" if row else "ALLOW"}

def safety_center_status():
    api = api_health_center()
    kill = emergency_kill_switch(False, "status_check")
    dup = duplicate_order_protection()
    webull_ok = api.get("webull_status", {}).get("status") in {"READY_SAFE", "READY"}
    score = 90 if webull_ok else 70
    return {"ok": True, "version": V550_VERSION, "safety_score": score, "api_health": api, "kill_switch": kill, "duplicate_order": dup}
