
from __future__ import annotations
from typing import Dict, Any
from .common import default_positions

LIQUIDITY_SCORE = {"US_EQUITY": 90, "GOLD": 85, "CASH": 100, "CRYPTO": 60, "TACTICAL": 70}

def tail_risk_detector() -> Dict[str, Any]:
    positions = default_positions()
    tail_score = 0
    reasons = []
    for p in positions:
        asset = p["asset"]
        weight = float(p["weight"])
        if asset == "CRYPTO" and weight > 10:
            tail_score += 20; reasons.append("crypto_weight_high")
        if asset == "TACTICAL" and weight > 20:
            tail_score += 15; reasons.append("tactical_weight_high")
        if asset == "US_EQUITY" and weight > 60:
            tail_score += 20; reasons.append("equity_concentration_high")
    level = "HIGH" if tail_score >= 30 else "MEDIUM" if tail_score >= 15 else "LOW"
    return {"ok": True, "tail_score": tail_score, "level": level, "reasons": reasons}

def liquidity_risk() -> Dict[str, Any]:
    positions = default_positions()
    weighted = 0
    for p in positions:
        weighted += float(p["weight"]) * LIQUIDITY_SCORE.get(p["asset"], 60) / 100
    level = "LOW" if weighted >= 85 else "MEDIUM" if weighted >= 70 else "HIGH"
    return {"ok": True, "liquidity_score": round(weighted, 2), "level": level, "positions": positions}
