
from __future__ import annotations
from typing import Dict, Any, List
import math

def _score_from_series(prices: List[float]) -> float:
    if len(prices) < 30:
        return 50.0
    ret5 = (prices[-1] - prices[-6]) / prices[-6] * 100 if prices[-6] else 0
    ret20 = (prices[-1] - prices[-21]) / prices[-21] * 100 if prices[-21] else 0
    return max(0, min(100, 50 + ret5 * 4 + ret20 * 1.5))

def trend_following(symbol: str, prices: List[float]) -> Dict[str, Any]:
    score = _score_from_series(prices)
    signal = "BUY" if score >= 65 else "SELL" if score <= 35 else "WAIT"
    return {"strategy": "Trend Following", "symbol": symbol, "score": round(score,2), "signal": signal}

def mean_reversion(symbol: str, prices: List[float]) -> Dict[str, Any]:
    if len(prices) < 30:
        return {"strategy": "Mean Reversion", "symbol": symbol, "score": 50, "signal": "WAIT"}
    mean = sum(prices[-20:]) / 20
    dev = (prices[-1] - mean) / mean * 100 if mean else 0
    score = max(0, min(100, 50 - dev * 8))
    signal = "BUY" if score >= 70 else "SELL" if score <= 30 else "WAIT"
    return {"strategy": "Mean Reversion", "symbol": symbol, "score": round(score,2), "signal": signal}

def momentum(symbol: str, prices: List[float]) -> Dict[str, Any]:
    if len(prices) < 60:
        return {"strategy": "Momentum", "symbol": symbol, "score": 50, "signal": "WAIT"}
    ret60 = (prices[-1] - prices[-60]) / prices[-60] * 100 if prices[-60] else 0
    score = max(0, min(100, 50 + ret60 * 1.2))
    signal = "BUY" if score >= 65 else "SELL" if score <= 35 else "WAIT"
    return {"strategy": "Momentum", "symbol": symbol, "score": round(score,2), "signal": signal}

def breakout(symbol: str, prices: List[float]) -> Dict[str, Any]:
    if len(prices) < 55:
        return {"strategy": "Breakout", "symbol": symbol, "score": 50, "signal": "WAIT"}
    high = max(prices[-50:-1])
    low = min(prices[-50:-1])
    if prices[-1] > high:
        return {"strategy": "Breakout", "symbol": symbol, "score": 85, "signal": "BUY"}
    if prices[-1] < low:
        return {"strategy": "Breakout", "symbol": symbol, "score": 20, "signal": "SELL"}
    return {"strategy": "Breakout", "symbol": symbol, "score": 50, "signal": "WAIT"}

def run_all_strategies(symbol: str, prices: List[float]) -> Dict[str, Any]:
    results = [
        trend_following(symbol, prices),
        mean_reversion(symbol, prices),
        momentum(symbol, prices),
        breakout(symbol, prices),
    ]
    return {"ok": True, "symbol": symbol, "strategies": results}
