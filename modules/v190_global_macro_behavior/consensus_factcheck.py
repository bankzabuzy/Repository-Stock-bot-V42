
from __future__ import annotations
from .economic_ai import economic_ai
from .human_behavior_ai import human_behavior_ai
from .news_sentiment_ai import news_sentiment_ai
from .probability_engine import probability_engine

def multi_ai_consensus():
    econ = economic_ai()
    human = human_behavior_ai()
    news = news_sentiment_ai()
    probs = probability_engine()
    votes = []
    if econ.get("macro_regime") in {"LIQUIDITY_SUPPORT","MIXED_MACRO"}:
        votes.append("RISK_OK")
    else:
        votes.append("RISK_CAUTION")
    if human.get("fear_score",50) > 70:
        votes.append("RISK_CAUTION")
    elif human.get("greed_score",50) > 70:
        votes.append("RISK_OK_BUT_OVERHEATED")
    else:
        votes.append("RISK_NEUTRAL")
    votes.append("RISK_OK" if news.get("sentiment") == "POSITIVE" else "RISK_CAUTION" if news.get("sentiment") == "NEGATIVE" else "RISK_NEUTRAL")
    sp = probs.get("horizons",{}).get("1D",{}).get("SP500",{}).get("bias")
    votes.append("RISK_OK" if sp == "BULLISH" else "RISK_CAUTION" if sp == "BEARISH" else "RISK_NEUTRAL")
    caution = sum(1 for v in votes if "CAUTION" in v)
    ok = sum(1 for v in votes if "OK" in v)
    if ok >= 3:
        consensus = "HIGH_CONVICTION_RISK_ON"
    elif caution >= 3:
        consensus = "HIGH_CONVICTION_RISK_OFF"
    else:
        consensus = "DISAGREEMENT_OR_MIXED"
    return {"ok": True, "consensus": consensus, "votes": votes, "agreement_pct": round(max(ok,caution)/len(votes)*100,2)}

def fact_check_layer():
    cons = multi_ai_consensus()
    agreement = cons.get("agreement_pct", 0)
    if agreement >= 75:
        status = "CONSENSUS"
    elif agreement >= 50:
        status = "PARTIAL_CONSENSUS"
    else:
        status = "LOW_CONFIDENCE"
    return {"ok": True, "status": status, "consensus": cons, "warning": "หลีกเลี่ยงสรุปแรงเกินไปถ้าเป็น LOW_CONFIDENCE หรือ DISAGREEMENT"}
