
from __future__ import annotations
from datetime import datetime, timezone
import os, time, json
from .common import init_db, connect, env_bool, V550_VERSION
from .secret_manager import secret_manager_status

BROKERS = {
    "WEBULL": ["WEBULL_API_KEY", "WEBULL_SECRET_KEY", "WEBULL_ACCOUNT_ID"],
    "ALPACA": ["ALPACA_API_KEY", "ALPACA_SECRET_KEY"],
    "IBKR": ["IBKR_HOST", "IBKR_PORT"],
    "MT5": ["MT5_LOGIN"],
    "BINANCE": ["BINANCE_API_KEY"],
    "PAPER": [],
}

def broker_integration_status():
    init_db()
    allow_live = env_bool("ALLOW_LIVE_TRADING", "false")
    secrets = secret_manager_status()
    rows = []
    conn = connect(); cur = conn.cursor()
    for broker, keys in BROKERS.items():
        start = time.time()
        configured = broker == "PAPER" or all(bool(os.getenv(k)) for k in keys)
        safe_mode = True if broker != "PAPER" else False
        if broker == "WEBULL" and configured and allow_live:
            safe_mode = True  # still requires human approval; no direct live by default
        latency = round((time.time() - start)*1000, 2)
        status = "READY_PAPER" if broker == "PAPER" else "CONFIGURED_SAFE" if configured else "MISSING_SECRET"
        row = {"broker": broker, "configured": configured, "paper_supported": True, "live_supported": broker != "PAPER", "safe_mode": safe_mode, "status": status, "latency_ms": latency}
        rows.append(row)
        cur.execute("INSERT OR REPLACE INTO v550_broker_accounts(broker,configured,paper_supported,live_supported,safe_mode,last_status,latency_ms,error,updated_at,model_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (broker, 1 if configured else 0, 1, 1 if broker != "PAPER" else 0, 1 if safe_mode else 0, status, latency, "" if configured else "missing credentials", datetime.now(timezone.utc).isoformat(), V550_VERSION))
    conn.commit(); conn.close()
    webull = next((r for r in rows if r["broker"] == "WEBULL"), {})
    return {"ok": True, "version": V550_VERSION, "allow_live_trading_env": allow_live, "webull_configured": webull.get("configured", False), "brokers": rows, "secrets": secrets}
