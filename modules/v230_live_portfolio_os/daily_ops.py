
from __future__ import annotations
from datetime import datetime, timezone
from .common import init_db, connect, V230_VERSION
from .portfolio_book import portfolio_snapshot
from .risk_ops import portfolio_ops_risk
from .rebalance_engine import rebalance_plan

def daily_ops_report():
    init_db()
    snap = portfolio_snapshot()
    risk = portfolio_ops_risk()
    reb = rebalance_plan()
    report = {
        "ok": True,
        "version": V230_VERSION,
        "portfolio": snap,
        "risk": risk,
        "rebalance": reb,
        "ops_decision": "PAUSE_NEW_RISK" if risk.get("decision") == "REDUCE_RISK" else "NORMAL_OPERATION",
    }
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v230_portfolio_snapshots(created_at,total_market_value,total_unrealized_pnl,heat,exposure_report,risk_report,model_version) VALUES(?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), snap.get("total_market_value"), snap.get("total_unrealized_pnl"), snap.get("heat"), str(snap.get("exposure")), str(risk), V230_VERSION))
        conn.commit(); conn.close()
    except Exception:
        pass
    return report

def daily_ops_text():
    r = daily_ops_report()
    p = r["portfolio"]
    risk = r["risk"]
    reb = r["rebalance"]
    lines = [
        "📊 V230 LIVE PORTFOLIO OS",
        f"Portfolio MV: {p.get('total_market_value')} | Unreal PnL: {p.get('total_unrealized_pnl')}",
        f"Heat: {p.get('heat')}% | Exposure: {p.get('exposure')}",
        f"Risk: {risk.get('risk_level')} | Decision: {risk.get('decision')} | Breaches: {risk.get('breaches')}",
        f"Rebalance: {reb.get('decision')}",
        f"Ops Decision: {r.get('ops_decision')}",
        f"Version : {r.get('version')}",
    ]
    return "\n".join(lines)
