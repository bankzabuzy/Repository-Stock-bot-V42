
from __future__ import annotations
import os
from .common import safe_float

CORR_GROUPS = {
    "AI_TECH": {"NVDA","QQQ","AMD","TSM","MSFT","META","AAPL"},
    "CRYPTO": {"BTC","BTCUSDT","ETH","ETHUSDT","COIN","MSTR"},
    "GOLD_USD": {"GOLD","GC=F","XAUUSD","DXY","DX-Y.NYB"},
}

def _positions():
    raw = os.getenv("V200_POSITIONS", os.getenv("V110_POSITIONS", "NVDA:8,QQQ:12,TSM:6,THAI_GOLD:10,CASH:30"))
    out = []
    for p in raw.split(","):
        if ":" in p:
            s,w = p.split(":",1)
            out.append({"symbol": s.strip().upper(), "weight": safe_float(w,0) or 0})
    return out

def portfolio_heat_control():
    pos = _positions()
    heat = sum(abs(p["weight"]) for p in pos if p["symbol"] != "CASH")
    group_heat = {}
    for name, symbols in CORR_GROUPS.items():
        group_heat[name] = sum(abs(p["weight"]) for p in pos if p["symbol"] in symbols)
    breaches = []
    if heat > float(os.getenv("V200_MAX_HEAT", "40")):
        breaches.append("TOTAL_HEAT_HIGH")
    if group_heat.get("AI_TECH",0) > float(os.getenv("V200_MAX_AI_TECH_HEAT", "30")):
        breaches.append("AI_TECH_CORRELATION_HIGH")
    if group_heat.get("CRYPTO",0) > float(os.getenv("V200_MAX_CRYPTO_HEAT", "12")):
        breaches.append("CRYPTO_HEAT_HIGH")
    decision = "REDUCE_RISK" if breaches else "ALLOW"
    return {"ok": not breaches, "portfolio_heat": round(heat,2), "group_heat": group_heat, "breaches": breaches, "decision": decision, "positions": pos}
