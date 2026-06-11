
from __future__ import annotations
import os, sqlite3, json, math
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

V200_VERSION = "V200_AUTONOMOUS_RETAIL_FUND_PLATFORM_STABLE"

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
            CREATE TABLE IF NOT EXISTS v200_trade_dna (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT,
                signal_type TEXT,
                market_regime TEXT,
                human_behavior TEXT,
                macro_narrative TEXT,
                raw_confidence REAL,
                adjusted_confidence REAL,
                final_confidence REAL,
                outcome TEXT,
                pnl_r REAL,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v200_human_error_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                error_type TEXT,
                severity TEXT,
                symbol TEXT,
                message TEXT,
                recommendation TEXT,
                payload TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v200_fund_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                alert_type TEXT,
                grade TEXT,
                title TEXT,
                message TEXT,
                should_push_line INTEGER,
                status TEXT,
                payload TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v200_macro_memory (
                key TEXT PRIMARY KEY,
                description TEXT,
                impact_bias TEXT,
                last_seen TEXT,
                score REAL,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v200_shadow_modes (
                mode TEXT PRIMARY KEY,
                enabled INTEGER,
                last_signal TEXT,
                last_result TEXT,
                updated_at TEXT
            )
        """)
        conn.commit(); conn.close()
        return {"ok": True, "db": db_path()}
    except Exception as e:
        return {"ok": False, "db": db_path(), "error": str(e)}

def record_alert(alert_type: str, grade: str, title: str, message: str, should_push_line: bool, payload: Any=None) -> Dict[str, Any]:
    init_db()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO v200_fund_alerts(created_at,alert_type,grade,title,message,should_push_line,status,payload,model_version) VALUES(?,?,?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), alert_type, grade, title, message, 1 if should_push_line else 0, "CREATED", json.dumps(payload, ensure_ascii=False, default=str) if payload is not None else "", V200_VERSION))
        conn.commit(); rid = cur.lastrowid; conn.close()
        return {"ok": True, "alert_id": rid}
    except Exception as e:
        return {"ok": False, "error": str(e)}

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
        bid = safe_float(info.get("bid"))
        ask = safe_float(info.get("ask"))
        chg = ((p-prev)/prev*100) if p is not None and prev else None
        spread = (ask-bid) if ask is not None and bid is not None and ask >= bid else None
        return {"ok": p is not None, "symbol": symbol, "price": p, "previous_close": prev, "change_pct": round(chg,2) if chg is not None else None, "bid": bid, "ask": ask, "spread": spread}
    except Exception as e:
        return {"ok": False, "symbol": symbol, "error": str(e)}
