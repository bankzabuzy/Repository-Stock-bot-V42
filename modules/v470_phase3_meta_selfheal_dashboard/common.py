
from __future__ import annotations
import os, sqlite3, json, math, random
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

V470_VERSION = "V470_PHASE3_META_SELFHEAL_REPORT_DASHBOARD_STABLE"

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
        CREATE TABLE IF NOT EXISTS v470_meta_learning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            model_name TEXT,
            regime TEXT,
            accuracy REAL,
            weight REAL,
            sample_size INTEGER,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v470_self_healing_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            component TEXT,
            issue TEXT,
            action TEXT,
            status TEXT,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v470_fund_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            symbol TEXT,
            decision TEXT,
            why_buy TEXT,
            why_sell TEXT,
            why_wait TEXT,
            risk_explanation TEXT,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v470_investor_dashboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            nav REAL,
            cagr REAL,
            rolling_return REAL,
            drawdown REAL,
            profit_factor REAL,
            sharpe REAL,
            sortino REAL,
            exposure TEXT,
            report TEXT,
            model_version TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS v470_phase3_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            latest_version TEXT,
            compile_ok INTEGER,
            route_collision_count INTEGER,
            compatibility_ok INTEGER,
            phase3_score REAL,
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
