
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, safe_float, V390_VERSION

def capital_protection(drawdown=0, losing_days=0, profit_factor=1.2, volatility_level="NORMAL"):
    init_db()
    dd = abs(safe_float(drawdown, 0) or 0)
    losing_days = int(safe_float(losing_days, 0) or 0)
    pf = safe_float(profit_factor, 1.2) or 1.2
    vol = str(volatility_level or "NORMAL").upper()
    triggers = []
    risk_multiplier = 1.0
    action = "NORMAL"
    if dd >= 15:
        triggers.append("DD_OVER_15")
        risk_multiplier *= 0.15
        action = "KILL_SWITCH"
    elif dd >= 10:
        triggers.append("DD_OVER_10")
        risk_multiplier *= 0.35
        action = "PAUSE_AND_REVIEW"
    elif dd >= 8:
        triggers.append("DD_OVER_8")
        risk_multiplier *= 0.5
        action = "REDUCE_RISK"
    if losing_days >= 5:
        triggers.append("LOSS_5_DAYS")
        risk_multiplier *= 0.5
        action = "PAUSE_AND_REVIEW" if action == "NORMAL" else action
    if pf < 1:
        triggers.append("PF_BELOW_1")
        risk_multiplier *= 0.5
        action = "REDUCE_RISK" if action == "NORMAL" else action
    if vol in {"HIGH","EXTREME"}:
        triggers.append("VOLATILITY_HIGH")
        risk_multiplier *= 0.5
        action = "REDUCE_RISK" if action == "NORMAL" else action
    report = {"drawdown": dd, "losing_days": losing_days, "profit_factor": pf, "volatility_level": vol, "action": action, "risk_multiplier": round(risk_multiplier, 3), "triggers": triggers}
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v390_capital_protection(created_at,drawdown,losing_days,profit_factor,volatility_level,action,risk_multiplier,triggers,report,model_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), dd, losing_days, pf, vol, action, risk_multiplier, ",".join(triggers), json.dumps(report, ensure_ascii=False), V390_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V390_VERSION, **report}
