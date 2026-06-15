
from __future__ import annotations
import os, sqlite3, json, hmac, math
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

V130_VERSION = "V1419_MASTER_CLEAN_FINAL"

def now_th() -> str:
    return datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")

def safe_float(x: Any, default: Optional[float]=None) -> Optional[float]:
    try:
        if x is None:
            return default
        if isinstance(x, str):
            x = x.replace(",", "").replace("$", "").replace("฿", "").replace("%", "").strip()
            if not x or x.upper() in {"N/A","NONE","NULL"}:
                return default
        return float(x)
    except Exception:
        return default

def env_bool(name: str, default: str="false") -> bool:
    return os.getenv(name, default).lower() in {"1","true","yes","on"}

def db_path() -> str:
    return os.getenv("DB_PATH", "signals.db")

def connect():
    return sqlite3.connect(db_path())

def init_db() -> Dict[str, Any]:
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v130_readiness_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                check_name TEXT,
                status TEXT,
                score REAL,
                detail TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v130_capital_allocation (
                bucket TEXT PRIMARY KEY,
                target_weight REAL,
                current_weight REAL,
                drift REAL,
                action TEXT,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v130_rebalance_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT,
                side TEXT,
                target_weight REAL,
                current_weight REAL,
                order_status TEXT,
                reason TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v130_incident_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                severity TEXT,
                component TEXT,
                message TEXT,
                payload TEXT,
                resolved INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
        return {"ok": True, "db": db_path()}
    except Exception as e:
        return {"ok": False, "db": db_path(), "error": str(e)}

def log_incident(component: str, message: str, severity: str="WARN", payload: Any=None) -> Dict[str, Any]:
    init_db()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO v130_incident_log(created_at,severity,component,message,payload) VALUES(?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), severity, component, message, json.dumps(payload, ensure_ascii=False, default=str) if payload is not None else ""))
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return {"ok": True, "incident_id": rid}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_admin(token: str | None) -> Dict[str, Any]:
    expected = os.getenv("ADMIN_TOKEN", "")
    if not expected:
        return {"ok": False, "reason": "ADMIN_TOKEN_NOT_SET"}
    ok = hmac.compare_digest(str(token or ""), expected)
    return {"ok": ok, "reason": "OK" if ok else "INVALID_TOKEN"}
