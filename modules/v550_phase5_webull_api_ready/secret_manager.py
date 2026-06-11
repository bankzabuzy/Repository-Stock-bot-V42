
from __future__ import annotations
from datetime import datetime, timezone
from .common import init_db, connect, mask_secret, V550_VERSION
import os

REQUIRED_KEYS = [
    "WEBULL_API_KEY",
    "WEBULL_SECRET_KEY",
    "WEBULL_ACCOUNT_ID",
    "LINE_CHANNEL_ACCESS_TOKEN",
    "ADMIN_TOKEN",
]

OPTIONAL_KEYS = [
    "ALPACA_API_KEY",
    "ALPACA_SECRET_KEY",
    "IBKR_HOST",
    "IBKR_PORT",
    "MT5_LOGIN",
    "BINANCE_API_KEY",
]

def secret_manager_status():
    init_db()
    rows = []
    conn = connect(); cur = conn.cursor()
    for k in REQUIRED_KEYS + OPTIONAL_KEYS:
        val = os.getenv(k)
        present = bool(val)
        risk = "CRITICAL_MISSING" if k in REQUIRED_KEYS and not present else "OK" if present else "OPTIONAL_MISSING"
        row = {"key_name": k, "present": present, "masked_value": mask_secret(val), "risk_level": risk}
        rows.append(row)
        cur.execute("INSERT INTO v550_secret_audit(created_at,key_name,present,masked_value,risk_level,model_version) VALUES(?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), k, 1 if present else 0, row["masked_value"], risk, V550_VERSION))
    conn.commit(); conn.close()
    ready = all(r["present"] for r in rows if r["key_name"] in REQUIRED_KEYS)
    return {"ok": True, "version": V550_VERSION, "webull_ready": ready, "items": rows, "note": "ใช้ .env เท่านั้น ห้าม hardcode API key ลง source"}
