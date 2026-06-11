
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import uuid, json, os
from .common import init_db, connect, V550_VERSION
from .order_dryrun import order_dry_run

APPROVAL_MODES = {"SAFE", "SEMI_AUTO", "FULL_AUTO"}

def create_approval(symbol="SPY", side="BUY", qty=1, broker="WEBULL", mode="SAFE"):
    init_db()
    mode = mode.upper()
    if mode not in APPROVAL_MODES:
        mode = "SAFE"
    dry = order_dry_run(symbol, side, qty, broker)
    approval_id = "APP-" + uuid.uuid4().hex[:12].upper()
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    if dry.get("status") != "PASS_DRY_RUN":
        status = "BLOCKED_DRY_RUN"
    elif mode == "FULL_AUTO":
        status = "PENDING_POLICY_CHECK"
    else:
        status = "WAITING_HUMAN_APPROVAL"
    report = {"approval_id": approval_id, "dry_run": dry, "mode": mode, "status": status, "instruction": "ให้อนุมัติด้วย ADMIN_TOKEN ผ่าน endpoint เฉพาะหลังตรวจแล้ว"}
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v550_human_approval(approval_id,created_at,symbol,side,qty,broker,mode,status,expires_at,report,model_version) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (approval_id, datetime.now(timezone.utc).isoformat(), symbol.upper(), side.upper(), float(qty), broker.upper(), mode, status, expires.isoformat(), json.dumps(report, ensure_ascii=False, default=str), V550_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V550_VERSION, **report}

def approval_center_status():
    init_db()
    conn = connect(); conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM v550_human_approval ORDER BY created_at DESC LIMIT 20")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"ok": True, "version": V550_VERSION, "recent": rows, "policy": "SAFE default: AI proposes, human approves, live order remains blocked until final adapter validation"}
