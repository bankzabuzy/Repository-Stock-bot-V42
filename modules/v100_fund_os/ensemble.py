
from __future__ import annotations
from typing import Dict, Any, List
from .strategies import run_all_strategies

def ensemble_vote(symbol: str, prices: List[float]) -> Dict[str, Any]:
    res = run_all_strategies(symbol, prices)
    votes = res.get("strategies", [])
    buy = sum(1 for v in votes if v.get("signal") == "BUY")
    sell = sum(1 for v in votes if v.get("signal") == "SELL")
    avg_score = sum(float(v.get("score", 50)) for v in votes) / max(1, len(votes))
    if buy >= 3 and avg_score >= 65:
        signal = "STRONG_BUY"
    elif buy > sell:
        signal = "BUY"
    elif sell > buy:
        signal = "SELL"
    else:
        signal = "WAIT"
    confidence = min(95, max(35, avg_score + abs(buy-sell)*5))
    return {
        "ok": True,
        "symbol": symbol,
        "signal": signal,
        "confidence": round(confidence, 2),
        "avg_score": round(avg_score, 2),
        "votes": {"BUY": buy, "SELL": sell, "WAIT": len(votes)-buy-sell},
        "strategy_results": votes,
    }
