
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Dict, Any
from .common import V180_1_VERSION, now_th, init_db, connect
from .market_behavior import market_behavior

def _risk_center_payload() -> Dict[str, Any]:
    try:
        from modules.v170_advanced_risk_stress.risk_dashboard import build_v170_payload
        return build_v170_payload()
    except Exception as e:
        return {"ok": False, "error": str(e), "version": "V170_NOT_AVAILABLE"}

def forecast_decision() -> Dict[str, Any]:
    behavior = market_behavior()
    risk = _risk_center_payload()
    heat = (risk.get("risk_heatmap") or {}).get("overall_level", "UNKNOWN")
    regime = behavior.get("regime")
    fear = behavior.get("fear_score", 50)
    greed = behavior.get("greed_score", 50)

    if heat in {"CRITICAL", "HIGH"} and regime in {"RISK_OFF", "HIGH_VOLATILITY"}:
        bias = "DEFENSIVE_HOLD"
        action = "ลดความเสี่ยง, งดสัญญาณเกรดต่ำ, รอ volatility settle"
        probability = max(75, fear)
    elif regime == "RISK_ON" and heat in {"LOW", "MEDIUM", "UNKNOWN"}:
        bias = "SELECTIVE_RISK_ON"
        action = "เข้าเฉพาะ leader ที่ RS แข็ง พร้อม position sizing"
        probability = max(65, greed)
    elif regime == "HIGH_VOLATILITY":
        bias = "TACTICAL_WAIT"
        action = "รอ spread แคบลง, งดไล่ราคา, ใช้ confirmation"
        probability = 70
    else:
        bias = "MIXED_ROTATION"
        action = "เลือกเฉพาะตัวชัดเจน ลดจำนวนไม้ และรอ breadth ยืนยัน"
        probability = 58

    confidence = max(45, min(92, (abs(fear-50)+abs(greed-50))/2 + 50))

    return {
        "ok": True,
        "version": V180_1_VERSION,
        "time_th": now_th(),
        "market_behavior": behavior,
        "risk_center": {
            "version": risk.get("version"),
            "overall_risk": (risk.get("risk_heatmap") or {}).get("overall_level"),
            "worst_scenario": (risk.get("scenarios") or {}).get("worst_case"),
            "var_cvar": risk.get("portfolio_var_cvar"),
            "monte_carlo": risk.get("monte_carlo"),
        },
        "forecast": {
            "bias": bias,
            "probability": round(probability, 2),
            "confidence": round(confidence, 2),
            "tactical_action": action,
            "regime": regime,
            "crowd_behavior": behavior.get("crowd_behavior"),
        },
    }

def save_audit(compile_ok: bool=True, route_collision_count: int=0) -> Dict[str, Any]:
    init_db()
    payload = forecast_decision()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO v180_1_forecast_risk_audit(created_at,latest_version,risk_level,market_regime,crowd_behavior,compile_ok,route_collision_count,report) VALUES(?,?,?,?,?,?,?,?)",
                    (
                        datetime.now(timezone.utc).isoformat(),
                        V180_1_VERSION,
                        payload.get("risk_center",{}).get("overall_risk"),
                        payload.get("forecast",{}).get("regime"),
                        payload.get("forecast",{}).get("crowd_behavior"),
                        1 if compile_ok else 0,
                        route_collision_count,
                        json.dumps(payload, ensure_ascii=False, default=str),
                    ))
        conn.commit(); rid = cur.lastrowid; conn.close()
        return {"ok": True, "audit_id": rid, "payload": payload}
    except Exception as e:
        return {"ok": False, "error": str(e), "payload": payload}

def forecast_text() -> str:
    p = forecast_decision()
    b = p["market_behavior"]
    f = p["forecast"]
    r = p["risk_center"]
    worst = r.get("worst_scenario") or {}
    lines = [
        "🧠 V180.1 MARKET BEHAVIOR + V170 RISK STRESS BASE",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        "LATEST",
        f"Version: {p.get('version')}",
        "Base: V170 Risk Center + V180 Market Behavior Forecast",
        "",
        "MARKET BEHAVIOR",
        f"Regime: {f.get('regime')} | Crowd: {f.get('crowd_behavior')}",
        f"Fear: {b.get('fear_score')} | Greed: {b.get('greed_score')}",
        f"Participants: {b.get('participants')}",
        "",
        "RISK STRESS",
        f"Overall Risk: {r.get('overall_risk')}",
        f"Worst Scenario: {worst.get('scenario')} | Loss {worst.get('portfolio_loss_pct')}%",
        "",
        "FORECAST / TACTICAL RESPONSE",
        f"Bias: {f.get('bias')} | Probability: {f.get('probability')}% | Confidence: {f.get('confidence')}%",
        f"Action: {f.get('tactical_action')}",
        "",
        "Quick: /v180-1/forecast-json | /v180-1/audit | /v170/risk-center",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
