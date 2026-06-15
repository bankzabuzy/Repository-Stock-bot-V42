
from __future__ import annotations
import os, sqlite3, json, hmac
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

V120_VERSION = "V1419_MASTER_CLEAN_FINAL"

def now_th() -> str:
    return datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")

def safe_float(x: Any, default: Optional[float]=None) -> Optional[float]:
    try:
        if x is None:
            return default
        if isinstance(x, str):
            x = x.replace(",", "").replace("$", "").replace("฿", "").replace("%", "").strip()
            if not x or x.upper() in {"N/A", "NONE", "NULL"}:
                return default
        return float(x)
    except Exception:
        return default

def db_path() -> str:
    return os.getenv("DB_PATH", "signals.db")

def connect():
    return sqlite3.connect(db_path())

def init_db() -> Dict[str, Any]:
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v120_broker_accounts (
                broker TEXT PRIMARY KEY,
                enabled INTEGER,
                mode TEXT,
                connected INTEGER,
                last_check_at TEXT,
                message TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v120_order_intents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT,
                side TEXT,
                qty REAL,
                order_type TEXT,
                limit_price REAL,
                stop_price REAL,
                broker TEXT,
                mode TEXT,
                approval_status TEXT,
                reason TEXT,
                payload TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v120_order_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intent_id INTEGER,
                created_at TEXT NOT NULL,
                broker TEXT,
                status TEXT,
                order_id TEXT,
                filled_price REAL,
                filled_qty REAL,
                error TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v120_safety_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                component TEXT,
                severity TEXT,
                message TEXT,
                payload TEXT
            )
        """)
        conn.commit()
        conn.close()
        return {"ok": True, "db": db_path()}
    except Exception as e:
        return {"ok": False, "db": db_path(), "error": str(e)}

def env_bool(name: str, default: str="false") -> bool:
    return os.getenv(name, default).lower() in {"1","true","yes","on"}

def verify_admin(token: str | None) -> Dict[str, Any]:
    expected = os.getenv("ADMIN_TOKEN", "")
    if not expected:
        return {"ok": False, "reason": "ADMIN_TOKEN_NOT_SET"}
    return {"ok": hmac.compare_digest(str(token or ""), expected), "reason": "OK" if hmac.compare_digest(str(token or ""), expected) else "INVALID_TOKEN"}

def safety_event(component: str, message: str, severity: str="INFO", payload: Any=None) -> Dict[str, Any]:
    init_db()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO v120_safety_events(created_at,component,severity,message,payload) VALUES(?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), component, severity, message, json.dumps(payload, ensure_ascii=False, default=str) if payload is not None else ""))
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return {"ok": True, "event_id": rid}
    except Exception as e:
        return {"ok": False, "error": str(e)}
