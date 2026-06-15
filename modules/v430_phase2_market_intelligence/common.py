
from __future__ import annotations
import os, sqlite3, random, math, json
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

V430_VERSION = "V1419_MASTER_CLEAN_FINAL"

def now_th():
    return datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")

def safe_float(x: Any, default: Optional[float]=None):
    try:
        if x is None: return default
        if isinstance(x, str):
            x = x.replace(",", "").replace("$", "").replace("฿", "").replace("%", "").strip()
            if not x or x.upper() in {"N/A","NONE","NULL"}: return default
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
    cur.execute("CREATE TABLE IF NOT EXISTS v430_microstructure(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,symbol TEXT,liquidity_score REAL,absorption_score REAL,stop_hunt_score REAL,fake_breakout_score REAL,spoofing_score REAL,order_flow_bias TEXT,report TEXT,model_version TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v430_regime(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,symbol TEXT,regime TEXT,strategy_mapping TEXT,confidence REAL,report TEXT,model_version TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v430_agent_debate(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,symbol TEXT,final_decision TEXT,consensus_score REAL,confidence_penalty REAL,votes TEXT,report TEXT,model_version TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v430_digital_twin(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,symbol TEXT,scenario TEXT,pass_gate INTEGER,expected_loss REAL,var_95 REAL,cvar_95 REAL,report TEXT,model_version TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v430_phase2_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,latest_version TEXT,compile_ok INTEGER,route_collision_count INTEGER,compatibility_ok INTEGER,phase2_score REAL,report TEXT)")
    conn.commit(); conn.close()
    return {"ok": True, "db": db_path()}

def price(symbol: str):
    try:
        import yfinance as yf
        info = {}
        try: info = yf.Ticker(symbol).info or {}
        except Exception: info = {}
        p = safe_float(info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose"))
        prev = safe_float(info.get("previousClose"))
        chg = ((p-prev)/prev*100) if p is not None and prev else None
        return {"ok": p is not None, "symbol": symbol, "price": p, "previous_close": prev, "change_pct": round(chg,2) if chg is not None else None}
    except Exception as e:
        return {"ok": False, "symbol": symbol, "error": str(e)}
