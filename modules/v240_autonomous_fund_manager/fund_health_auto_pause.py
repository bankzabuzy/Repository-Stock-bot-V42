
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, V240_VERSION
from .capital_flow_regime import regime_switching

def _score_inverse_bad(level):
    if level in {"CRITICAL"}: return 20
    if level in {"HIGH"}: return 45
    if level in {"NORMAL","LOW"}: return 85
    return 65

def fund_health_score():
    init_db()
    try:
        from modules.v230_live_portfolio_os.risk_ops import portfolio_ops_risk
        risk = portfolio_ops_risk()
    except Exception as e:
        risk = {"risk_level": "HIGH", "error": str(e)}

    try:
        from modules.v200_autonomous_retail_fund.human_error_protection import human_error_protection
        human = human_error_protection()
    except Exception as e:
        human = {"severity": "HIGH", "error": str(e)}

    try:
        from modules.v220_broker_execution_network.broker_network import broker_status
        broker = broker_status()
    except Exception as e:
        broker = {"items": [], "error": str(e)}

    regime = regime_switching()

    risk_score = _score_inverse_bad(risk.get("risk_level"))
    portfolio_score = 100 if risk.get("decision") != "REDUCE_RISK" else 55
    macro_score = 80 if regime.get("regime") == "RISK_ON" else 55 if regime.get("regime") == "MIXED" else 35
    execution_score = 80 if any(b.get("broker") == "PAPER" and b.get("enabled") for b in broker.get("items", [])) else 40
    human_score = 85 if human.get("severity") == "LOW" else 45
    health = round(risk_score*0.25 + portfolio_score*0.25 + macro_score*0.2 + execution_score*0.15 + human_score*0.15, 2)
    decision = "AUTO_PAUSE" if health < 50 or risk.get("risk_level") in {"CRITICAL"} else "REDUCE_RISK" if health < 65 else "NORMAL"
    payload = {"risk": risk, "human": human, "broker": broker, "regime": regime}
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v240_fund_health(created_at,health_score,risk_score,portfolio_score,macro_score,execution_score,human_score,decision,report,model_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), health, risk_score, portfolio_score, macro_score, execution_score, human_score, decision, json.dumps(payload, ensure_ascii=False, default=str), V240_VERSION))
        conn.commit(); conn.close()
    except Exception:
        pass
    return {"ok": True, "health_score": health, "decision": decision, "components": {"risk": risk_score, "portfolio": portfolio_score, "macro": macro_score, "execution": execution_score, "human": human_score}, "payload": payload}

def auto_pause_engine():
    h = fund_health_score()
    triggers = []
    if h.get("decision") == "AUTO_PAUSE":
        triggers.append("fund_health_below_threshold")
    risk = h.get("payload",{}).get("risk",{})
    if risk.get("risk_level") == "CRITICAL":
        triggers.append("critical_portfolio_risk")
    return {"ok": True, "active": bool(triggers), "triggers": triggers, "fund_health": h}
