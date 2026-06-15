
from __future__ import annotations
import os, sqlite3, math, random, json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

V170_VERSION = "V1419_MASTER_CLEAN_FINAL"

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
            CREATE TABLE IF NOT EXISTS v170_stress_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                scenario_name TEXT,
                portfolio_loss_pct REAL,
                var_95 REAL,
                cvar_95 REAL,
                max_drawdown REAL,
                risk_level TEXT,
                report TEXT,
                model_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v170_risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                component TEXT,
                severity TEXT,
                message TEXT,
                payload TEXT
            )
        """)
        conn.commit(); conn.close()
        return {"ok": True, "db": db_path()}
    except Exception as e:
        return {"ok": False, "db": db_path(), "error": str(e)}

def log_event(component: str, message: str, severity: str="INFO", payload: Any=None) -> Dict[str, Any]:
    init_db()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO v170_risk_events(created_at,component,severity,message,payload) VALUES(?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), component, severity, message, json.dumps(payload, ensure_ascii=False, default=str) if payload is not None else ""))
        conn.commit(); rid = cur.lastrowid; conn.close()
        return {"ok": True, "event_id": rid}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def percentile(values: List[float], q: float) -> Optional[float]:
    if not values:
        return None
    vals = sorted(values)
    idx = max(0, min(len(vals)-1, int(len(vals)*q)))
    return vals[idx]

def default_positions() -> List[Dict[str, Any]]:
    raw = os.getenv("V170_POSITIONS", os.getenv("V110_POSITIONS", "US_EQUITY:45,GOLD:20,CASH:20,CRYPTO:5,TACTICAL:10"))
    out = []
    for p in raw.split(","):
        if ":" in p:
            k, v = p.split(":", 1)
            out.append({"asset": k.strip().upper(), "weight": safe_float(v, 0) or 0})
    return out
