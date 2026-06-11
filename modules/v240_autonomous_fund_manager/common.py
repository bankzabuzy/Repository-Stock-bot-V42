
from __future__ import annotations
import os, sqlite3, json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

V240_VERSION = "V240_AUTONOMOUS_FUND_MANAGER_STABLE"

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

def init_db() -> Dict[str, Any]:
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v240_investment_committee (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT,
                final_decision TEXT,
                final_score REAL,
                committee_report TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v240_fund_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                health_score REAL,
                risk_score REAL,
                portfolio_score REAL,
                macro_score REAL,
                execution_score REAL,
                human_score REAL,
                decision TEXT,
                report TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v240_institutional_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event_type TEXT,
                symbol TEXT,
                decision TEXT,
                reason TEXT,
                macro_context TEXT,
                regime TEXT,
                payload TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v240_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                latest_version TEXT,
                compile_ok INTEGER,
                route_collision_count INTEGER,
                compatibility_ok INTEGER,
                report TEXT
            )
        """)
        conn.commit(); conn.close()
        return {"ok": True, "db": db_path()}
    except Exception as e:
        return {"ok": False, "db": db_path(), "error": str(e)}

def price(symbol: str) -> Dict[str, Any]:
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        info = {}
        try:
            info = t.info or {}
        except Exception:
            info = {}
        p = safe_float(info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose"))
        prev = safe_float(info.get("previousClose"))
        chg = ((p-prev)/prev*100) if p is not None and prev else None
        return {"ok": p is not None, "symbol": symbol, "price": p, "previous_close": prev, "change_pct": round(chg,2) if chg is not None else None}
    except Exception as e:
        return {"ok": False, "symbol": symbol, "error": str(e)}
