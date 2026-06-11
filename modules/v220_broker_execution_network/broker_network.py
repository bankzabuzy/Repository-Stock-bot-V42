
from __future__ import annotations
import os, uuid, json
from datetime import datetime, timezone
from typing import Dict, Any
from .common import init_db, connect, env_bool, V220_VERSION

BROKERS = {
    "PAPER": {"asset_classes": ["US_STOCK","ETF","GOLD_PROXY","CRYPTO"], "env": []},
    "IBKR": {"asset_classes": ["US_STOCK","ETF","OPTIONS","FUTURES"], "env": ["IBKR_HOST","IBKR_PORT"]},
    "ALPACA": {"asset_classes": ["US_STOCK","ETF","OPTIONS"], "env": ["ALPACA_API_KEY","ALPACA_SECRET_KEY"]},
    "MT5": {"asset_classes": ["FX","XAUUSD","CFD"], "env": ["MT5_LOGIN","MT5_SERVER"]},
    "BINANCE": {"asset_classes": ["CRYPTO"], "env": ["BINANCE_API_KEY","BINANCE_API_SECRET"]},
}

def broker_status() -> Dict[str, Any]:
    init_db()
    items = []
    for name, meta in BROKERS.items():
        configured = name == "PAPER" or all(bool(os.getenv(k)) for k in meta["env"])
        safe_mode = not env_bool("ALLOW_LIVE_TRADING") or name != os.getenv("BROKER_DEFAULT","PAPER").upper()
        enabled = name == "PAPER" or configured
        item = {
            "broker": name,
            "enabled": enabled,
            "configured": configured,
            "safe_mode": safe_mode,
            "asset_classes": meta["asset_classes"],
            "status": "READY_SIM" if name == "PAPER" else "CONFIGURED_SAFE" if configured else "MISSING_CONFIG",
        }
        items.append(item)
    try:
        conn = connect(); cur = conn.cursor()
        for i in items:
            cur.execute("INSERT OR REPLACE INTO v220_broker_network(broker,enabled,configured,safe_mode,asset_classes,last_status,updated_at) VALUES(?,?,?,?,?,?,?)",
                        (i["broker"], int(i["enabled"]), int(i["configured"]), int(i["safe_mode"]), json.dumps(i["asset_classes"]), i["status"], datetime.now(timezone.utc).isoformat()))
        conn.commit(); conn.close()
    except Exception:
        pass
    return {"ok": True, "version": V220_VERSION, "allow_live_trading": env_bool("ALLOW_LIVE_TRADING"), "items": items}

def classify_symbol(symbol: str) -> str:
    s = symbol.upper()
    if s in {"SPY","QQQ","NVDA","AAPL","MSFT","TSLA","AMD","TSM","META"}:
        return "US_STOCK"
    if s in {"XAUUSD","GC=F","GOLD","THAI_GOLD"}:
        return "GOLD_PROXY"
    if s.endswith("USDT") or s in {"BTC","ETH","BTCUSDT","ETHUSDT"}:
        return "CRYPTO"
    return "UNKNOWN"

def choose_broker(symbol: str, preferred: str="PAPER") -> Dict[str, Any]:
    asset = classify_symbol(symbol)
    status = broker_status()["items"]
    pref = preferred.upper()
    candidates = [b for b in status if b["broker"] == pref and asset in b["asset_classes"] and b["enabled"]]
    if not candidates:
        candidates = [b for b in status if asset in b["asset_classes"] and b["enabled"]]
    broker = candidates[0]["broker"] if candidates else "PAPER"
    return {"ok": True, "symbol": symbol.upper(), "asset_class": asset, "broker": broker, "reason": "preferred_available" if broker == pref else "fallback_selected"}
