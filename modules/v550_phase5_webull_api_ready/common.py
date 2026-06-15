
from __future__ import annotations
import os, sqlite3, json, hashlib, hmac, math, time
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

V550_VERSION = "V1419_MASTER_CLEAN_FINAL"

def now_th():
    return datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")

def safe_float(x: Any, default: Optional[float]=None):
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

def env_bool(name: str, default="false"):
    return str(os.getenv(name, default)).lower() in {"1","true","yes","on"}

def db_path():
    return os.getenv("DB_PATH", "signals.db")

def connect():
    return sqlite3.connect(db_path())

def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v550_broker_accounts (
            broker TEXT PRIMARY KEY,
            configured INTEGER,
            paper_supported INTEGER,
            live_supported INTEGER,
            safe_mode INTEGER,
            last_status TEXT,
            latency_ms REAL,
            error TEXT,
            updated_at TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v550_secret_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            key_name TEXT,
            present INTEGER,
            masked_value TEXT,
            risk_level TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v550_order_dryrun (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            broker TEXT,
            symbol TEXT,
            side TEXT,
            qty REAL,
            estimated_price REAL,
            estimated_slippage REAL,
            estimated_commission REAL,
            notional REAL,
            status TEXT,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v550_human_approval (
            approval_id TEXT PRIMARY KEY,
            created_at TEXT,
            symbol TEXT,
            side TEXT,
            qty REAL,
            broker TEXT,
            mode TEXT,
            status TEXT,
            expires_at TEXT,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v550_api_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            broker TEXT,
            status TEXT,
            latency_ms REAL,
            token_status TEXT,
            reconnect_action TEXT,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v550_safety_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            event_type TEXT,
            severity TEXT,
            action TEXT,
            status TEXT,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v550_phase5_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            latest_version TEXT,
            compile_ok INTEGER,
            route_collision_count INTEGER,
            compatibility_ok INTEGER,
            phase5_score REAL,
            report TEXT
        )
    """)
    conn.commit()
    conn.close()
    return {"ok": True, "db": db_path()}

def mask_secret(value: str | None):
    if not value:
        return ""
    v = str(value)
    if len(v) <= 6:
        return "***"
    return v[:3] + "***" + v[-3:]

def price(symbol: str):
    try:
        import yfinance as yf
        info = {}
        try:
            info = yf.Ticker(symbol).info or {}
        except Exception:
            info = {}
        p = safe_float(info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose"))
        prev = safe_float(info.get("previousClose"))
        chg = ((p-prev)/prev*100) if p is not None and prev else None
        return {"ok": p is not None, "symbol": symbol, "price": p, "previous_close": prev, "change_pct": round(chg,2) if chg is not None else None}
    except Exception as e:
        return {"ok": False, "symbol": symbol, "error": str(e)}
