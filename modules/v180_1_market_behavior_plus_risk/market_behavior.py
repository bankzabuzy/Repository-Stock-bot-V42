
from __future__ import annotations
from typing import Dict, Any
from .common import get_price_snapshot

def market_behavior() -> Dict[str, Any]:
    spy = get_price_snapshot("SPY")
    qqq = get_price_snapshot("QQQ")
    vix = get_price_snapshot("^VIX")
    gold = get_price_snapshot("GC=F")
    dxy = get_price_snapshot("DX-Y.NYB")

    changes = {
        "SPY": spy.get("change_pct") or 0,
        "QQQ": qqq.get("change_pct") or 0,
        "VIX": vix.get("change_pct") or 0,
        "GOLD": gold.get("change_pct") or 0,
        "DXY": dxy.get("change_pct") or 0,
    }
    fear_score = max(0, min(100, 50 + changes["VIX"]*4 - changes["SPY"]*5 - changes["QQQ"]*4 + max(0, changes["DXY"])*2))
    greed_score = max(0, min(100, 50 + changes["SPY"]*5 + changes["QQQ"]*4 - changes["VIX"]*3))

    if fear_score >= 70:
        crowd = "FEAR / DE-RISKING"
        regime = "RISK_OFF"
    elif greed_score >= 70:
        crowd = "GREED / RISK-ON CHASING"
        regime = "RISK_ON"
    elif changes["VIX"] > 3:
        crowd = "VOLATILITY_REPRICING"
        regime = "HIGH_VOLATILITY"
    elif abs(changes["SPY"]) < 0.25 and abs(changes["QQQ"]) < 0.25:
        crowd = "WAIT_AND_SEE / LOW CONVICTION"
        regime = "MIXED"
    else:
        crowd = "MIXED / SECTOR ROTATION"
        regime = "MIXED"

    participants = {
        "retail": "fomo_buying" if "GREED" in crowd else "panic_or_waiting" if "FEAR" in crowd else "mixed_chasing",
        "institution": "rotate_or_de-risk" if regime != "RISK_ON" else "selective_risk_on",
        "market_maker": "widen_spread" if regime == "HIGH_VOLATILITY" else "range_control",
    }

    return {
        "ok": True,
        "regime": regime,
        "crowd_behavior": crowd,
        "fear_score": round(fear_score, 2),
        "greed_score": round(greed_score, 2),
        "changes": changes,
        "participants": participants,
        "snapshots": {"SPY": spy, "QQQ": qqq, "VIX": vix, "GOLD": gold, "DXY": dxy},
    }
