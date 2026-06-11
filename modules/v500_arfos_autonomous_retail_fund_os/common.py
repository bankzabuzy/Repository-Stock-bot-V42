
from __future__ import annotations
import os, sqlite3, json, math
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

V500_VERSION = "V500_ARFOS_AUTONOMOUS_RETAIL_FUND_OS_STABLE"

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

def db_path():
    return os.getenv("DB_PATH", "signals.db")

def connect():
    return sqlite3.connect(db_path())

def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v500_shadow_real_money (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            symbol TEXT,
            ai_decision TEXT,
            human_decision TEXT,
            benchmark_decision TEXT,
            ai_pnl_r REAL,
            human_pnl_r REAL,
            benchmark_pnl_r REAL,
            divergence_score REAL,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v500_governance_policy (
            policy_key TEXT PRIMARY KEY,
            policy_value TEXT,
            severity TEXT,
            enabled INTEGER,
            updated_at TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v500_arfos_core (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            system_mode TEXT,
            readiness_score REAL,
            live_allowed INTEGER,
            paper_allowed INTEGER,
            broker_allowed INTEGER,
            decision TEXT,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v500_phase4_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            latest_version TEXT,
            compile_ok INTEGER,
            route_collision_count INTEGER,
            compatibility_ok INTEGER,
            phase4_score REAL,
            report TEXT
        )
    """)
    conn.commit()
    conn.close()
    return {"ok": True, "db": db_path()}

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
