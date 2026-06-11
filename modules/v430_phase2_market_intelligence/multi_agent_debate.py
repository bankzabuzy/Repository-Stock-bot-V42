
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, price, safe_float, V430_VERSION
from .microstructure_ai import market_microstructure
from .regime_ai import regime_ai

def _vote_from_score(score):
    if score >= 65: return "BUY"
    if score <= 40: return "SELL"
    return "WAIT"

def multi_agent_debate(symbol="SPY"):
    init_db()
    snap = price(symbol)
    chg = safe_float(snap.get("change_pct"),0) or 0
    micro = market_microstructure(symbol)
    regime = regime_ai(symbol)

    technical_score = max(0, min(100, 50 + chg*8))
    macro_score = 70 if regime.get("regime") == "RISK_ON" else 35 if regime.get("regime") in {"RISK_OFF","PANIC"} else 55
    risk_score = 30 if regime.get("regime") in {"PANIC","HIGH_VOLATILITY"} else 65
    sentiment_score = max(0, min(100, 50 + chg*5))
    options_flow_score = 60 if micro.get("order_flow_bias") == "BUY_PRESSURE" else 40 if micro.get("order_flow_bias") == "SELL_PRESSURE" else 50

    votes = [
        {"agent": "Technical AI", "vote": _vote_from_score(technical_score), "confidence": round(technical_score,2), "reason": f"momentum {chg}%"},
        {"agent": "Macro AI", "vote": _vote_from_score(macro_score), "confidence": macro_score, "reason": f"regime {regime.get('regime')}"},
        {"agent": "Risk AI", "vote": "WAIT" if risk_score < 50 else "BUY", "confidence": risk_score, "reason": "risk gate from regime"},
        {"agent": "Sentiment AI", "vote": _vote_from_score(sentiment_score), "confidence": round(sentiment_score,2), "reason": "price sentiment proxy"},
        {"agent": "Options Flow AI", "vote": _vote_from_score(options_flow_score), "confidence": options_flow_score, "reason": "order-flow proxy"},
    ]
    counts = {"BUY":0,"SELL":0,"WAIT":0}
    for v in votes:
        counts[v["vote"]] += 1
    final = max(counts, key=counts.get)
    consensus = counts[final]/len(votes)*100
    penalty = 0 if consensus >= 80 else 10 if consensus >= 60 else 25
    if final == "BUY" and any(v["agent"]=="Risk AI" and v["vote"]=="WAIT" for v in votes):
        final = "WAIT"
        penalty += 10
    report = {"symbol": symbol, "final_decision": final, "consensus_score": round(consensus,2), "confidence_penalty": penalty, "counts": counts, "votes": votes, "microstructure": micro, "regime": regime}
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v430_agent_debate(created_at,symbol,final_decision,consensus_score,confidence_penalty,votes,report,model_version) VALUES(?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), symbol.upper(), final, consensus, penalty, json.dumps(votes, ensure_ascii=False), json.dumps(report, ensure_ascii=False, default=str), V430_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V430_VERSION, **report}
