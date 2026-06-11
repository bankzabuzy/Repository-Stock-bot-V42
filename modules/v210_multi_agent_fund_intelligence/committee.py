
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, V210_VERSION
from .agents import run_agents

def committee_decision(symbol: str="SPY") -> dict:
    init_db()
    data = run_agents(symbol)
    votes = data.get("votes", [])
    counts = {"BUY":0, "SELL":0, "WAIT":0}
    for v in votes:
        counts[v.get("vote","WAIT")] = counts.get(v.get("vote","WAIT"),0)+1
    total = max(1, len(votes))
    majority_vote = max(counts, key=counts.get)
    agreement = counts[majority_vote] / total * 100
    avg_conf = sum(float(v.get("confidence",0)) for v in votes)/total
    risk_vote = next((v for v in votes if v.get("agent") == "Risk AI"), {})
    execution_vote = next((v for v in votes if v.get("agent") == "Execution AI"), {})
    override = None
    if risk_vote.get("vote") == "WAIT":
        override = "RISK_BLOCK"
        final = "WAIT"
    elif execution_vote.get("vote") == "WAIT":
        override = "EXECUTION_BLOCK"
        final = "WAIT"
    elif agreement < 60:
        override = "LOW_CONSENSUS"
        final = "WAIT"
    else:
        final = majority_vote

    final_conf = min(95, max(20, avg_conf * (agreement/100)))
    report = {
        "symbol": symbol,
        "counts": counts,
        "agreement_pct": round(agreement,2),
        "avg_confidence": round(avg_conf,2),
        "final_decision": final,
        "final_confidence": round(final_conf,2),
        "risk_override": override,
        "votes": votes,
    }
    try:
        conn = connect(); cur = conn.cursor()
        for v in votes:
            cur.execute("INSERT INTO v210_agent_votes(created_at,agent_name,symbol,vote,confidence,reasoning,payload,model_version) VALUES(?,?,?,?,?,?,?,?)",
                        (datetime.now(timezone.utc).isoformat(), v.get("agent"), symbol, v.get("vote"), v.get("confidence"), v.get("reasoning"), json.dumps(v.get("payload",{}), ensure_ascii=False, default=str), V210_VERSION))
        cur.execute("INSERT INTO v210_committee_decisions(created_at,symbol,final_decision,final_confidence,disagreement_score,risk_override,report,model_version) VALUES(?,?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), symbol, final, final_conf, 100-agreement, override, json.dumps(report, ensure_ascii=False, default=str), V210_VERSION))
        conn.commit(); conn.close()
    except Exception:
        pass
    return {"ok": True, "version": V210_VERSION, **report}
