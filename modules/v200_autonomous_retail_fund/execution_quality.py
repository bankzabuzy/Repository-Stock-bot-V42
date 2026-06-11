
from __future__ import annotations
from .common import price, safe_float

def execution_quality_monitor(symbol: str="SPY"):
    snap = price(symbol)
    spread = safe_float(snap.get("spread"))
    p = safe_float(snap.get("price"))
    spread_pct = (spread / p * 100) if spread is not None and p else None
    abnormal = spread_pct is not None and spread_pct > 0.25
    quality = "POOR" if abnormal else "GOOD" if snap.get("ok") else "UNKNOWN"
    decision = "NO_TRADE_SPREAD_HIGH" if abnormal else "ALLOW"
    return {"ok": True, "symbol": symbol, "quality": quality, "spread": spread, "spread_pct": round(spread_pct,4) if spread_pct is not None else None, "decision": decision, "snapshot": snap}
