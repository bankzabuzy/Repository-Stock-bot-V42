
from __future__ import annotations
from .common import price

def black_swan_detector():
    vix = price("^VIX").get("change_pct") or 0
    spy = price("SPY").get("change_pct") or 0
    gold = price("GC=F").get("change_pct") or 0
    dxy = price("DX-Y.NYB").get("change_pct") or 0
    triggers = []
    if vix > 12 and spy < -2:
        triggers.append("flash_crash_or_vol_shock")
    if gold > 2 and dxy > 1:
        triggers.append("geopolitical_or_safe_haven_shock")
    if spy < -3 and dxy > 1.5:
        triggers.append("liquidity_stress")
    level = "HIGH" if len(triggers) >= 2 else "MEDIUM" if triggers else "LOW"
    return {"ok": True, "level": level, "triggers": triggers, "inputs": {"VIX":vix,"SPY":spy,"GOLD":gold,"DXY":dxy}}
