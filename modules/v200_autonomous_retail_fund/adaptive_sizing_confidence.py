
from __future__ import annotations
from .portfolio_heat_correlation import portfolio_heat_control
from .execution_quality import execution_quality_monitor

def adaptive_position_sizing(base_risk_pct: float=1.0, regime: str="MIXED", black_swan_level: str="LOW"):
    risk = base_risk_pct
    if regime in {"HIGH_VOLATILITY","RISK_OFF"}:
        risk *= 0.5
    if black_swan_level in {"MEDIUM"}:
        risk *= 0.5
    if black_swan_level == "HIGH":
        risk *= 0.25
    heat = portfolio_heat_control()
    if heat.get("decision") == "REDUCE_RISK":
        risk *= 0.5
    return {"ok": True, "base_risk_pct": base_risk_pct, "final_risk_pct": round(max(0.1, risk), 3), "reason": {"regime": regime, "black_swan": black_swan_level, "heat": heat.get("decision")}}

def confidence_calibration(raw_confidence: float=75, macro_penalty: float=0, execution_penalty: float=0, human_penalty: float=0):
    adjusted = raw_confidence - macro_penalty
    final = adjusted - execution_penalty - human_penalty
    final = max(0, min(100, final))
    grade = "A+" if final >= 90 else "A" if final >= 85 else "B+" if final >= 80 else "NO_ALERT"
    return {"ok": True, "raw_confidence": raw_confidence, "adjusted_confidence": round(adjusted,2), "final_confidence": round(final,2), "grade": grade, "penalties": {"macro": macro_penalty, "execution": execution_penalty, "human": human_penalty}}
