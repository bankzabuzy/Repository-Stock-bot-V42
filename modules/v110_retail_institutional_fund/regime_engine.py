
from __future__ import annotations
from typing import Dict, Any
from .common import get_yfinance_price, safe_float

def market_regime() -> Dict[str, Any]:
    spy = get_yfinance_price("SPY")
    qqq = get_yfinance_price("QQQ")
    vix = get_yfinance_price("^VIX")
    gold = get_yfinance_price("GC=F")
    def chg(x):
        p = safe_float(x.get("price")); prev = safe_float(x.get("previous_close"))
        return (p-prev)/prev*100 if p is not None and prev else 0
    spy_c, qqq_c, vix_c, gold_c = chg(spy), chg(qqq), chg(vix), chg(gold)
    score = 50 + spy_c*5 + qqq_c*4 - vix_c*3 + gold_c*1
    if score >= 65:
        regime = "RISK_ON"
    elif score <= 40:
        regime = "RISK_OFF"
    elif vix_c > 5:
        regime = "HIGH_VOLATILITY"
    else:
        regime = "MIXED"
    return {
        "ok": True,
        "regime": regime,
        "score": round(max(0, min(100, score)), 2),
        "changes": {"SPY": round(spy_c,2), "QQQ": round(qqq_c,2), "VIX": round(vix_c,2), "GOLD": round(gold_c,2)},
        "rule": "Risk On/Off จาก SPY QQQ VIX Gold",
    }
