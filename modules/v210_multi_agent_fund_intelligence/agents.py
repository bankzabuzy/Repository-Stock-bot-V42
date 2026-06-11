
from __future__ import annotations
from typing import Dict, Any, List
from .common import price

def _vote_from_score(score: float) -> str:
    if score >= 65: return "BUY"
    if score <= 40: return "SELL"
    return "WAIT"

def technical_agent(symbol: str="SPY") -> Dict[str, Any]:
    snap = price(symbol)
    chg = snap.get("change_pct") or 0
    score = max(0, min(100, 50 + chg*8))
    return {"agent": "Technical AI", "symbol": symbol, "vote": _vote_from_score(score), "confidence": round(score,2), "reasoning": f"price momentum {chg}%"}

def macro_agent(symbol: str="SPY") -> Dict[str, Any]:
    try:
        from modules.v190_global_macro_behavior.economic_ai import economic_ai
        econ = economic_ai()
        regime = econ.get("macro_regime")
    except Exception as e:
        econ = {"error": str(e)}; regime = "UNKNOWN"
    score = 65 if regime in {"LIQUIDITY_SUPPORT","MIXED_MACRO"} else 45 if regime in {"INFLATION_COMEBACK"} else 35 if regime in {"RECESSION_FEAR","STAGFLATION_RISK"} else 50
    return {"agent": "Macro AI", "symbol": symbol, "vote": _vote_from_score(score), "confidence": score, "reasoning": f"macro regime {regime}", "payload": econ}

def behavior_agent(symbol: str="SPY") -> Dict[str, Any]:
    try:
        from modules.v190_global_macro_behavior.human_behavior_ai import human_behavior_ai
        h = human_behavior_ai()
    except Exception as e:
        h = {"error": str(e), "fear_score": 50, "greed_score": 50}
    fear = h.get("fear_score",50); greed = h.get("greed_score",50)
    score = 65 if greed > 65 and fear < 60 else 45 if fear > 70 else 55
    return {"agent": "Behavior AI", "symbol": symbol, "vote": _vote_from_score(score), "confidence": round(score,2), "reasoning": f"fear {fear} greed {greed}", "payload": h}

def risk_agent(symbol: str="SPY") -> Dict[str, Any]:
    try:
        from modules.v200_autonomous_retail_fund.kill_switch_shadow_alerts import emergency_kill_switch
        k = emergency_kill_switch(symbol)
    except Exception as e:
        k = {"error": str(e), "active": False}
    score = 25 if k.get("active") else 65
    return {"agent": "Risk AI", "symbol": symbol, "vote": "WAIT" if k.get("active") else "BUY", "confidence": score, "reasoning": f"kill switch active={k.get('active')}", "payload": k}

def execution_agent(symbol: str="SPY") -> Dict[str, Any]:
    try:
        from modules.v200_autonomous_retail_fund.execution_quality import execution_quality_monitor
        q = execution_quality_monitor(symbol)
    except Exception as e:
        q = {"error": str(e), "decision": "UNKNOWN"}
    score = 35 if q.get("decision") != "ALLOW" else 70
    return {"agent": "Execution AI", "symbol": symbol, "vote": "WAIT" if q.get("decision") != "ALLOW" else "BUY", "confidence": score, "reasoning": f"execution quality {q.get('quality')}", "payload": q}

def run_agents(symbol: str="SPY") -> Dict[str, Any]:
    votes = [
        technical_agent(symbol),
        macro_agent(symbol),
        behavior_agent(symbol),
        risk_agent(symbol),
        execution_agent(symbol),
    ]
    return {"ok": True, "symbol": symbol, "votes": votes}
