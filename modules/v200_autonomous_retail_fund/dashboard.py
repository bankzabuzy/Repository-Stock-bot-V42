
from __future__ import annotations
from .common import V200_VERSION, now_th, init_db
from .human_error_protection import human_error_protection
from .portfolio_heat_correlation import portfolio_heat_control
from .execution_quality import execution_quality_monitor
from .adaptive_sizing_confidence import adaptive_position_sizing, confidence_calibration
from .trade_dna_self_learning import self_learning_weight_engine
from .macro_memory_factcheck import macro_memory, multi_ai_factcheck_consensus
from .kill_switch_shadow_alerts import emergency_kill_switch, shadow_mode_status, institutional_line_alert

def _v190_macro():
    try:
        from modules.v190_global_macro_behavior.dashboard import build_v190_payload
        return build_v190_payload()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def build_v200_payload(symbol: str="SPY"):
    init_db()
    macro = _v190_macro()
    regime = ((macro.get("economic_ai") or {}).get("macro_regime") or "MIXED")
    black = ((macro.get("black_swan_detector") or {}).get("level") or "LOW")
    human = human_error_protection({"symbol": symbol})
    heat = portfolio_heat_control()
    execq = execution_quality_monitor(symbol)
    sizing = adaptive_position_sizing(1.0, "RISK_OFF" if "RECESSION" in regime or "STAG" in regime else "MIXED", black)
    exec_penalty = 10 if execq.get("decision") != "ALLOW" else 0
    human_penalty = 15 if human.get("decision") != "ALLOW" else 0
    macro_penalty = 10 if "RISK" in regime or "STAG" in regime else 0
    conf = confidence_calibration(82, macro_penalty, exec_penalty, human_penalty)
    kill = emergency_kill_switch(symbol)
    alert = institutional_line_alert("V200 FUND SIGNAL CHECK", 86, conf.get("final_confidence",0), "A" if conf.get("grade") in {"A","A+"} else "B", 2.2, {"symbol": symbol})
    return {
        "ok": True,
        "version": V200_VERSION,
        "time_th": now_th(),
        "symbol": symbol,
        "macro_v190": macro,
        "human_error_protection": human,
        "portfolio_heat": heat,
        "execution_quality": execq,
        "adaptive_position_sizing": sizing,
        "confidence_calibration": conf,
        "self_learning": self_learning_weight_engine(),
        "macro_memory": macro_memory(),
        "factcheck_consensus": multi_ai_factcheck_consensus(),
        "emergency_kill_switch": kill,
        "shadow_mode": shadow_mode_status(),
        "institutional_line_alert": alert,
        "endpoints": ["/v200/fund-manager", "/v200/fund-manager-json", "/v200/human-error", "/v200/kill-switch", "/v200/line-alert-test"],
    }

def build_v200_text(symbol: str="SPY"):
    p = build_v200_payload(symbol)
    heat = p["portfolio_heat"]
    human = p["human_error_protection"]
    conf = p["confidence_calibration"]
    kill = p["emergency_kill_switch"]
    alert = p["institutional_line_alert"]
    macro = p["macro_v190"]
    lines = [
        "🏛️ V200 AUTONOMOUS RETAIL FUND PLATFORM",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        "MISSION",
        "ลดความผิดพลาดของคน + คุมความเสี่ยง + ใช้ Macro/Behavior/Risk เป็น Decision Support",
        "",
        "GLOBAL MACRO / BEHAVIOR",
        f"Macro: {(macro.get('economic_ai') or {}).get('macro_regime')} | Narrative: {(macro.get('market_narrative') or {}).get('narrative')}",
        "",
        "HUMAN ERROR PROTECTION",
        f"Decision: {human.get('decision')} | Severity: {human.get('severity')} | Issues: {human.get('issues')}",
        "",
        "PORTFOLIO HEAT / CORRELATION",
        f"Heat: {heat.get('portfolio_heat')}% | Decision: {heat.get('decision')} | Breaches: {heat.get('breaches')}",
        "",
        "CONFIDENCE / POSITION SIZING",
        f"Raw: {conf.get('raw_confidence')} | Final: {conf.get('final_confidence')} | Grade: {conf.get('grade')}",
        f"Risk Size: {p.get('adaptive_position_sizing',{}).get('final_risk_pct')}%",
        "",
        "KILL SWITCH / SHADOW",
        f"Kill Switch: {'ACTIVE' if kill.get('active') else 'OK'} | Triggers: {kill.get('triggers')}",
        f"Shadow: {p.get('shadow_mode',{}).get('modes')}",
        "",
        "LINE ALERT",
        f"Should Push: {alert.get('should_push_line')} | Grade: {alert.get('grade')}",
        "",
        "สำคัญ: ระบบนี้ช่วยลดข้อผิดพลาดและเพิ่มวินัย แต่ไม่สามารถรับประกันกำไรหรือชนะตลาดได้ทุกครั้ง",
        "Quick: /v200/fund-manager-json | /v200/kill-switch | /v200/human-error",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
