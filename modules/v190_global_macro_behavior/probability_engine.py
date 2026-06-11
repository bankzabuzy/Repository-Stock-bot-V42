
from __future__ import annotations
from .common import price
from .economic_ai import economic_ai
from .human_behavior_ai import human_behavior_ai
from .news_sentiment_ai import news_sentiment_ai

ASSETS = {"SP500":"SPY", "NASDAQ":"QQQ", "GOLD":"GC=F", "USD":"DX-Y.NYB", "OIL":"CL=F"}

def _asset_prob(symbol):
    snap = price(symbol)
    chg = snap.get("change_pct") or 0
    base = 50 + chg*5
    return max(5, min(95, base))

def probability_engine():
    econ = economic_ai()
    human = human_behavior_ai()
    news = news_sentiment_ai()
    horizons = {}
    for h, damp in [("1D", 1.0), ("1W", 0.75), ("1M", 0.55)]:
        items = {}
        for name, sym in ASSETS.items():
            p = _asset_prob(sym)
            # macro adjustments
            macro = econ.get("macro_regime")
            if name in {"SP500","NASDAQ"} and macro in {"RECESSION_FEAR","STAGFLATION_RISK"}:
                p -= 10*damp
            if name == "GOLD" and human.get("fear_score",50) > 65:
                p += 8*damp
            if name == "USD" and macro in {"INFLATION_COMEBACK","STAGFLATION_RISK"}:
                p += 6*damp
            if news.get("sentiment") == "NEGATIVE" and name in {"SP500","NASDAQ"}:
                p -= 6*damp
            p = max(5, min(95, p))
            items[name] = {"bull_probability": round(p,2), "bear_probability": round(100-p,2), "bias": "BULLISH" if p>=58 else "BEARISH" if p<=42 else "NEUTRAL"}
        horizons[h] = items
    return {"ok": True, "horizons": horizons, "inputs": {"macro": econ.get("macro_regime"), "fear": human.get("fear_score"), "greed": human.get("greed_score"), "news": news.get("sentiment")}}
