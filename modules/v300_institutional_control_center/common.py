
from __future__ import annotations
import os, sqlite3, json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

V300_VERSION = "V300_INSTITUTIONAL_CONTROL_CENTER_STABLE"

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
            CREATE TABLE IF NOT EXISTS v300_data_bus_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                topic TEXT,
                symbol TEXT,
                payload TEXT,
                freshness_sec REAL,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v300_feature_store (
                feature_key TEXT PRIMARY KEY,
                symbol TEXT,
                feature_group TEXT,
                feature_value REAL,
                feature_payload TEXT,
                updated_at TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v300_model_registry (
                model_id TEXT PRIMARY KEY,
                model_name TEXT,
                model_type TEXT,
                owner_layer TEXT,
                version TEXT,
                enabled INTEGER,
                health_score REAL,
                drift_score REAL,
                notes TEXT,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v300_explainability_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT,
                decision TEXT,
                explanation TEXT,
                factor_report TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v300_control_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                latest_version TEXT,
                compile_ok INTEGER,
                route_collision_count INTEGER,
                compatibility_ok INTEGER,
                system_score REAL,
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
