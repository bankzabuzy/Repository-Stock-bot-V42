
from __future__ import annotations
import os, sqlite3, json, time
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
V350_VERSION="V1419_MASTER_CLEAN_FINAL"
def now_th(): return datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")
def safe_float(x:Any, default:Optional[float]=None):
    try:
        if x is None: return default
        if isinstance(x,str):
            x=x.replace(",","").replace("$","").replace("฿","").replace("%","").strip()
            if not x or x.upper() in {"N/A","NONE","NULL"}: return default
        return float(x)
    except Exception: return default
def db_path(): return os.getenv("DB_PATH","signals.db")
def connect(): return sqlite3.connect(db_path())
def init_db():
    conn=connect(); cur=conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS v350_route_registry(route TEXT PRIMARY KEY,file TEXT,status TEXT,collision_count INTEGER,updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v350_provider_health(provider TEXT PRIMARY KEY,enabled INTEGER,priority INTEGER,health_score REAL,latency_ms REAL,last_status TEXT,last_error TEXT,updated_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v350_provider_prices(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,symbol TEXT,provider TEXT,price REAL,previous_close REAL,data_age_sec REAL,status TEXT,payload TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v350_forward_tests(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,signal_id TEXT,symbol TEXT,side TEXT,entry_price REAL,current_price REAL,horizon_days INTEGER,age_days REAL,mae REAL,mfe REAL,rr REAL,status TEXT,result_r REAL,payload TEXT,model_version TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v350_performance_proof(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,window_days INTEGER,winrate REAL,profit_factor REAL,sharpe REAL,sortino REAL,calmar REAL,max_dd REAL,expectancy REAL,sample_size INTEGER,report TEXT,model_version TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v350_line_alerts(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,alert_key TEXT,grade TEXT,title TEXT,message TEXT,status TEXT,retry_count INTEGER,cooldown_until TEXT,payload TEXT,model_version TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v350_production_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,latest_version TEXT,compile_ok INTEGER,route_collision_count INTEGER,provider_ok INTEGER,forward_test_ok INTEGER,performance_ok INTEGER,line_governance_ok INTEGER,production_score REAL,report TEXT)")
    conn.commit(); conn.close()
    return {"ok":True,"db":db_path()}
def price_yahoo(symbol):
    try:
        import yfinance as yf
        info={}
        try: info=yf.Ticker(symbol).info or {}
        except Exception: info={}
        p=safe_float(info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose"))
        prev=safe_float(info.get("previousClose"))
        return {"ok":p is not None,"provider":"Yahoo","symbol":symbol,"price":p,"previous_close":prev}
    except Exception as e:
        return {"ok":False,"provider":"Yahoo","symbol":symbol,"error":str(e)}
