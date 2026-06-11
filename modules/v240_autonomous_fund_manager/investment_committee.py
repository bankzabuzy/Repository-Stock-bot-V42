
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, V240_VERSION

def _safe_call(path, default):
    try:
        mod_name, fn_name = path.rsplit(".", 1)
        mod = __import__(mod_name, fromlist=[fn_name])
        return getattr(mod, fn_name)()
    except Exception as e:
        return {**default, "error": str(e)}

def investment_committee(symbol: str="SPY") -> dict:
    init_db()
    try:
        from modules.v210_multi_agent_fund_intelligence.committee import committee_decision
        agent = committee_decision(symbol)
    except Exception as e:
        agent = {"final_decision": "WAIT", "final_confidence": 40, "error": str(e)}

    try:
        from modules.v230_live_portfolio_os.risk_ops import portfolio_ops_risk
        risk = portfolio_ops_risk()
    except Exception as e:
        risk = {"decision": "REDUCE_RISK", "risk_level": "UNKNOWN", "error": str(e)}

    try:
        from modules.v190_global_macro_behavior.dashboard import build_v190_payload
        macro = build_v190_payload()
    except Exception as e:
        macro = {"economic_ai": {"macro_regime": "UNKNOWN"}, "error": str(e)}

    try:
        from modules.v200_autonomous_retail_fund.kill_switch_shadow_alerts import emergency_kill_switch
        kill = emergency_kill_switch(symbol)
    except Exception as e:
        kill = {"active": True, "error": str(e)}

    votes = {
        "CIO_AI": agent.get("final_decision", "WAIT"),
        "Risk_Manager_AI": "WAIT" if risk.get("decision") == "REDUCE_RISK" else "ALLOW",
        "Macro_Manager_AI": "WAIT" if str((macro.get("economic_ai") or {}).get("macro_regime")).upper() in {"RECESSION_FEAR","STAGFLATION_RISK"} else "ALLOW",
        "Execution_Manager_AI": "WAIT" if kill.get("active") else "ALLOW",
        "Portfolio_Manager_AI": "WAIT" if risk.get("risk_level") in {"HIGH","CRITICAL"} else "ALLOW",
    }
    wait_count = sum(1 for v in votes.values() if v == "WAIT")
    buy_like = agent.get("final_decision") in {"BUY","STRONG_BUY"} and wait_count == 0
    final = "APPROVED_BUY" if buy_like else "WAIT"
    score = max(0, min(100, float(agent.get("final_confidence", 50)) - wait_count*15))
    report = {"symbol": symbol, "votes": votes, "agent": agent, "risk": risk, "macro_regime": (macro.get("economic_ai") or {}).get("macro_regime"), "kill_switch": kill}
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v240_investment_committee(created_at,symbol,final_decision,final_score,committee_report,model_version) VALUES(?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), symbol, final, score, json.dumps(report, ensure_ascii=False, default=str), V240_VERSION))
        conn.commit(); conn.close()
    except Exception:
        pass
    return {"ok": True, "version": V240_VERSION, "symbol": symbol, "final_decision": final, "final_score": round(score,2), "votes": votes, "report": report}
