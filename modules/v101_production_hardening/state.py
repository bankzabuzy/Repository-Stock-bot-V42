
from __future__ import annotations
import os, sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List

V101_VERSION = "V1419_MASTER_CLEAN_FINAL"

def db_path() -> str:
    return os.getenv("DB_PATH", "signals.db")

def connect():
    return sqlite3.connect(db_path())

def init_state_db() -> Dict[str, Any]:
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v101_system_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v101_error_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                component TEXT,
                severity TEXT,
                message TEXT,
                detail TEXT,
                resolved INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v101_system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event_type TEXT,
                message TEXT,
                payload TEXT
            )
        """)
        conn.commit(); conn.close()
        return {"ok": True, "db": db_path()}
    except Exception as e:
        return {"ok": False, "db": db_path(), "error": str(e)}

def set_state(key: str, value: str) -> Dict[str, Any]:
    init_state_db()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO v101_system_state(key,value,updated_at) VALUES(?,?,?)",
                    (key, value, datetime.now(timezone.utc).isoformat()))
        conn.commit(); conn.close()
        return {"ok": True, "key": key, "value": value}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_state(key: str, default: str = "") -> str:
    init_state_db()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT value FROM v101_system_state WHERE key=?", (key,))
        row = cur.fetchone(); conn.close()
        return row[0] if row else default
    except Exception:
        return default

def log_error(component: str, message: str, detail: str = "", severity: str = "ERROR") -> Dict[str, Any]:
    init_state_db()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO v101_error_registry(created_at,component,severity,message,detail) VALUES(?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), component, severity, message, detail))
        conn.commit(); rid = cur.lastrowid; conn.close()
        return {"ok": True, "error_id": rid}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def last_errors(limit: int = 10) -> Dict[str, Any]:
    init_state_db()
    try:
        conn = connect(); conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM v101_error_registry ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"ok": True, "items": rows}
    except Exception as e:
        return {"ok": False, "error": str(e), "items": []}

def event(event_type: str, message: str, payload: str = "") -> Dict[str, Any]:
    init_state_db()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO v101_system_events(created_at,event_type,message,payload) VALUES(?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), event_type, message, payload))
        conn.commit(); rid = cur.lastrowid; conn.close()
        return {"ok": True, "event_id": rid}
    except Exception as e:
        return {"ok": False, "error": str(e)}
