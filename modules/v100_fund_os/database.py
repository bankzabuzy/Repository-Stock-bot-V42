
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List
from .config import get_config, V100_VERSION

def connect():
    return sqlite3.connect(get_config().db_path)

def init_db() -> Dict[str, Any]:
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fund_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                asset_class TEXT,
                strategy TEXT,
                signal TEXT,
                confidence REAL,
                probability REAL,
                risk_grade TEXT,
                decision TEXT,
                reason TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fund_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                broker TEXT,
                mode TEXT,
                symbol TEXT NOT NULL,
                side TEXT,
                qty REAL,
                price REAL,
                status TEXT,
                order_id TEXT,
                error TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fund_positions (
                symbol TEXT PRIMARY KEY,
                asset_class TEXT,
                qty REAL,
                avg_price REAL,
                last_price REAL,
                market_value REAL,
                unrealized_pnl REAL,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fund_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event_type TEXT,
                message TEXT,
                payload TEXT,
                severity TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fund_research_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                experiment_name TEXT,
                status TEXT,
                metrics TEXT,
                notes TEXT,
                model_version TEXT
            )
        """)
        conn.commit()
        conn.close()
        return {"ok": True, "db": get_config().db_path}
    except Exception as e:
        return {"ok": False, "db": get_config().db_path, "error": str(e)}

def audit(event_type: str, message: str, payload: str = "", severity: str = "INFO") -> Dict[str, Any]:
    init_db()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO fund_audit_logs(created_at,event_type,message,payload,severity,model_version) VALUES(?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), event_type, message, payload, severity, V100_VERSION)
        )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return {"ok": True, "audit_id": rid}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def last_audit(limit: int = 10) -> Dict[str, Any]:
    init_db()
    try:
        conn = connect()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM fund_audit_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"ok": True, "items": rows}
    except Exception as e:
        return {"ok": False, "error": str(e), "items": []}
