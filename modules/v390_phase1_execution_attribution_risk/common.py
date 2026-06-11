
from __future__ import annotations
import os, sqlite3, json, math
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

V390_VERSION = "V390_PHASE1_EXECUTION_ATTRIBUTION_RISK_STABLE"

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
        CREATE TABLE IF NOT EXISTS v390_execution_verification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            broker TEXT,
            symbol TEXT,
            side TEXT,
            expected_price REAL,
            filled_price REAL,
            qty REAL,
            status TEXT,
            broker_reject_reason TEXT,
            partial_fill INTEGER,
            slippage REAL,
            latency_ms REAL,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v390_attribution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            symbol TEXT,
            strategy TEXT,
            macro_regime TEXT,
            contribution_r REAL,
            contribution_pct REAL,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v390_position_sizing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            symbol TEXT,
            method TEXT,
            base_risk REAL,
            volatility REAL,
            winrate REAL,
            payoff REAL,
            suggested_risk REAL,
            suggested_qty REAL,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v390_capital_protection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            drawdown REAL,
            losing_days INTEGER,
            profit_factor REAL,
            volatility_level TEXT,
            action TEXT,
            risk_multiplier REAL,
            triggers TEXT,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v390_phase1_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            latest_version TEXT,
            compile_ok INTEGER,
            route_collision_count INTEGER,
            compatibility_ok INTEGER,
            phase1_score REAL,
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
        return {"ok": p is not None, "symbol": symbol, "price": p, "previous_close": prev}
    except Exception as e:
        return {"ok": False, "symbol": symbol, "error": str(e)}
