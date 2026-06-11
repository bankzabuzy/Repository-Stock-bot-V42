
from __future__ import annotations
from .portfolio_book import portfolio_snapshot

def portfolio_ops_risk():
    p = portfolio_snapshot()
    exposure = p.get("exposure", {})
    heat = p.get("heat", 0)
    breaches = []
    if heat > 70:
        breaches.append("PORTFOLIO_HEAT_OVER_70")
    if exposure.get("US_STOCK",0) + exposure.get("ETF",0) > 70:
        breaches.append("EQUITY_EXPOSURE_HIGH")
    if exposure.get("CRYPTO",0) > 10:
        breaches.append("CRYPTO_EXPOSURE_HIGH")
    if exposure.get("CASH",0) < 10:
        breaches.append("CASH_BELOW_10")
    level = "CRITICAL" if len(breaches) >= 3 else "HIGH" if breaches else "NORMAL"
    decision = "REDUCE_RISK" if breaches else "ALLOW"
    return {"ok": True, "risk_level": level, "decision": decision, "breaches": breaches, "snapshot": p}
