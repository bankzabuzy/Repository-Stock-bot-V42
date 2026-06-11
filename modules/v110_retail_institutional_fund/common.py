
from __future__ import annotations
import os, sqlite3, math, random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

V110_VERSION = "V110_RETAIL_INSTITUTIONAL_FUND_PLATFORM_STABLE"

def now_th() -> str:
    return datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")

def safe_float(x: Any, default: Optional[float]=None) -> Optional[float]:
    try:
        if x is None:
            return default
        if isinstance(x, str):
            x = x.replace(",", "").replace("$", "").replace("฿", "").replace("%", "").strip()
            if not x or x.upper() in {"N/A", "NONE", "NULL"}:
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
            CREATE TABLE IF NOT EXISTS v110_execution_sim (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT,
                expected_price REAL,
                filled_price REAL,
                side TEXT,
                qty REAL,
                spread REAL,
                slippage REAL,
                commission REAL,
                delay_ms INTEGER,
                status TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v110_model_registry (
                model_id TEXT PRIMARY KEY,
                model_name TEXT,
                model_type TEXT,
                version TEXT,
                weight REAL,
                enabled INTEGER,
                last_score REAL,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v110_strategy_scoreboard (
                strategy TEXT PRIMARY KEY,
                win_rate REAL,
                profit_factor REAL,
                sharpe REAL,
                max_dd REAL,
                enabled INTEGER,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v110_shadow_portfolio (
                portfolio_name TEXT,
                symbol TEXT,
                weight REAL,
                last_pnl REAL,
                updated_at TEXT,
                PRIMARY KEY(portfolio_name, symbol)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v110_daily_reports (
                report_date TEXT PRIMARY KEY,
                report_text TEXT,
                created_at TEXT,
                model_version TEXT
            )
        """)
        conn.commit()
        conn.close()
        return {"ok": True, "db": db_path()}
    except Exception as e:
        return {"ok": False, "db": db_path(), "error": str(e)}

def clamp(x: Any, low: float=0, high: float=100) -> float:
    v = safe_float(x, low)
    if v is None:
        v = low
    return max(low, min(high, float(v)))

def try_import(path: str):
    try:
        module_name, func_name = path.rsplit(".", 1)
        mod = __import__(module_name, fromlist=[func_name])
        return getattr(mod, func_name), None
    except Exception as e:
        return None, str(e)

def get_yfinance_price(symbol: str) -> Dict[str, Any]:
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        info = {}
        try:
            info = t.info or {}
        except Exception:
            info = {}
        price = safe_float(info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose"))
        prev = safe_float(info.get("previousClose"))
        pre = safe_float(info.get("preMarketPrice"))
        post = safe_float(info.get("postMarketPrice"))
        return {"ok": price is not None, "symbol": symbol.upper(), "price": price, "previous_close": prev, "pre_market": pre, "after_hours": post, "source": "Yahoo Finance"}
    except Exception as e:
        return {"ok": False, "symbol": symbol.upper(), "error": str(e), "source": "Yahoo Finance"}
