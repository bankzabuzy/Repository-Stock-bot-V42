
from __future__ import annotations
import os, sqlite3, json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

V230_VERSION = "V230_LIVE_PORTFOLIO_OS_STABLE"

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
            CREATE TABLE IF NOT EXISTS v230_live_positions (
                symbol TEXT PRIMARY KEY,
                asset_class TEXT,
                qty REAL,
                avg_price REAL,
                last_price REAL,
                market_value REAL,
                unrealized_pnl REAL,
                realized_pnl REAL,
                risk_bucket TEXT,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v230_portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                total_market_value REAL,
                total_unrealized_pnl REAL,
                heat REAL,
                exposure_report TEXT,
                risk_report TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v230_rebalance_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT,
                action TEXT,
                current_weight REAL,
                target_weight REAL,
                drift REAL,
                status TEXT,
                reason TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v230_ops_audit (
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
