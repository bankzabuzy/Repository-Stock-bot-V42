
from __future__ import annotations
import os, sqlite3, json, hmac
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

V220_VERSION = "V1419_MASTER_CLEAN_FINAL"

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

def db_path() -> str:
    return os.getenv("DB_PATH", "signals.db")

def connect():
    return sqlite3.connect(db_path())

def env_bool(name: str, default: str="false") -> bool:
    return os.getenv(name, default).lower() in {"1","true","yes","on"}

def verify_admin(token: str | None) -> Dict[str, Any]:
    expected = os.getenv("ADMIN_TOKEN", "")
    if not expected:
        return {"ok": False, "reason": "ADMIN_TOKEN_NOT_SET"}
    ok = hmac.compare_digest(str(token or ""), expected)
    return {"ok": ok, "reason": "OK" if ok else "INVALID_TOKEN"}

def init_db() -> Dict[str, Any]:
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v220_broker_network (
                broker TEXT PRIMARY KEY,
                enabled INTEGER,
                configured INTEGER,
                safe_mode INTEGER,
                asset_classes TEXT,
                last_status TEXT,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v220_execution_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT,
                side TEXT,
                qty REAL,
                broker TEXT,
                mode TEXT,
                pretrade_status TEXT,
                routing_status TEXT,
                result TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v220_compatibility_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                latest_version TEXT,
                compile_ok INTEGER,
                route_collision_count INTEGER,
                required_modules_ok INTEGER,
                report TEXT
            )
        """)
        conn.commit(); conn.close()
        return {"ok": True, "db": db_path()}
    except Exception as e:
        return {"ok": False, "db": db_path(), "error": str(e)}
