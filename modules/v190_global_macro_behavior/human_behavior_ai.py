
from __future__ import annotations
from .common import price

def human_behavior_ai():
    spy, qqq, vix = price("SPY"), price("QQQ"), price("^VIX")
    spyc = spy.get("change_pct") or 0
    qqqc = qqq.get("change_pct") or 0
    vixc = vix.get("change_pct") or 0
    fear = max(0, min(100, 50 + vixc*5 - spyc*6 - qqqc*4))
    greed = max(0, min(100, 50 + spyc*6 + qqqc*4 - vixc*4))

    retail = "FOMO_BUYING" if greed > 70 else "PANIC_SELLING_OR_HEDGING" if fear > 70 else "WAIT_AND_SEE"
    institution = "ROTATION_ACCUMULATION" if spyc > 0 and vixc <= 0 else "DE_RISKING" if fear > 70 else "SELECTIVE_POSITIONING"
    market_maker = "GAMMA_PINNING" if abs(spyc) < 0.3 and abs(vixc) < 2 else "VOL_EXPANSION" if vixc > 4 else "SPREAD_CONTROL"
    politician = "POLICY_HEADLINE_RISK_MONITOR" 
    central_bank = "RATE_PATH_SENSITIVE"

    return {
        "ok": True,
        "fear_score": round(fear,2),
        "greed_score": round(greed,2),
        "actors": {
            "retail": retail,
            "institution": institution,
            "market_maker": market_maker,
            "politicians": politician,
            "central_bank": central_bank,
        },
        "edge": "ใช้ฝูงชนเป็น contrarian filter เมื่อ fear/greed สุดโต่ง และใช้ institution/market maker เป็นตัวกรองจังหวะเข้า",
    }
