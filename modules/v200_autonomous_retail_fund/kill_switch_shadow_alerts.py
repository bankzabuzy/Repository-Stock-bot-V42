
from __future__ import annotations
from datetime import datetime, timezone
from .common import init_db, connect, record_alert, V200_VERSION
from .portfolio_heat_correlation import portfolio_heat_control
from .execution_quality import execution_quality_monitor
from .human_error_protection import human_error_protection

def emergency_kill_switch(symbol: str="SPY"):
    heat = portfolio_heat_control()
    execq = execution_quality_monitor(symbol)
    human = human_error_protection({"symbol": symbol, "portfolio_heat": heat.get("portfolio_heat")})
    triggers = []
    if heat.get("decision") == "REDUCE_RISK":
        triggers.append("portfolio_heat")
    if execq.get("decision") != "ALLOW":
        triggers.append("execution_quality")
    if human.get("decision") == "BLOCK_NEW_TRADES":
        triggers.append("human_error")
    active = len(triggers) > 0
    return {"ok": True, "active": active, "triggers": triggers, "decision": "STOP_NEW_TRADES" if active else "ALLOW"}

def shadow_mode_status():
    init_db()
    modes = [("REAL",0),("PAPER",1),("EXPERIMENT",1)]
    try:
        conn = connect(); cur = conn.cursor()
        for m,en in modes:
            cur.execute("INSERT OR IGNORE INTO v200_shadow_modes(mode,enabled,last_signal,last_result,updated_at) VALUES(?,?,?,?,?)",
                        (m,en,None,None,datetime.now(timezone.utc).isoformat()))
        conn.commit(); conn.close()
    except Exception:
        pass
    return {"ok": True, "modes": [{"mode":m,"enabled":bool(en)} for m,en in modes], "note": "REAL disabled by default; PAPER/EXPERIMENT enabled for validation"}

def institutional_line_alert(title: str, probability: float, confidence: float, risk_grade: str, rr: float, details: dict | None=None):
    should = probability >= 85 and confidence >= 85 and risk_grade in {"A","A+"} and rr >= 2
    grade = "A+" if probability >= 90 and confidence >= 90 else "A" if should else "NO_ALERT"
    message = f"🔥 {title}\nProbability {probability}%\nConfidence {confidence}%\nRisk {risk_grade}\nRR 1:{rr}\nDecision: {'SEND_LINE' if should else 'HOLD'}"
    rec = record_alert("INSTITUTIONAL_LINE", grade, title, message, should, details or {})
    return {"ok": True, "should_push_line": should, "grade": grade, "message": message, "record": rec}
