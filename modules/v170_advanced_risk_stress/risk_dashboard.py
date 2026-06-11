
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Dict, Any
from .common import V170_VERSION, now_th, init_db, connect
from .scenario_engine import run_all_scenarios
from .monte_carlo import monte_carlo_stress
from .portfolio_risk import portfolio_var_cvar, correlation_matrix
from .tail_liquidity import tail_risk_detector, liquidity_risk
from .recovery import drawdown_recovery_analysis

def risk_heatmap() -> Dict[str, Any]:
    scen = run_all_scenarios()
    mc = monte_carlo_stress(3000)
    var = portfolio_var_cvar()
    tail = tail_risk_detector()
    liq = liquidity_risk()
    components = [
        {"component": "Scenario Worst", "level": scen.get("worst_case",{}).get("risk_level")},
        {"component": "Portfolio VaR", "level": var.get("risk_level")},
        {"component": "Tail Risk", "level": tail.get("level")},
        {"component": "Liquidity", "level": liq.get("level")},
    ]
    score_map = {"LOW": 25, "MEDIUM": 55, "HIGH": 80, "CRITICAL": 95}
    score = round(sum(score_map.get(c.get("level"), 50) for c in components)/len(components), 2)
    overall = "CRITICAL" if score >= 90 else "HIGH" if score >= 75 else "MEDIUM" if score >= 45 else "LOW"
    return {"ok": True, "overall_score": score, "overall_level": overall, "components": components}

def build_v170_payload() -> Dict[str, Any]:
    init_db()
    payload = {
        "ok": True,
        "version": V170_VERSION,
        "time_th": now_th(),
        "scenarios": run_all_scenarios(),
        "monte_carlo": monte_carlo_stress(),
        "portfolio_var_cvar": portfolio_var_cvar(),
        "correlation_matrix": correlation_matrix(),
        "tail_risk": tail_risk_detector(),
        "liquidity_risk": liquidity_risk(),
        "drawdown_recovery": drawdown_recovery_analysis(),
        "risk_heatmap": risk_heatmap(),
    }
    try:
        worst = payload["scenarios"].get("worst_case", {})
        conn = connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO v170_stress_runs(created_at,scenario_name,portfolio_loss_pct,var_95,cvar_95,max_drawdown,risk_level,report,model_version) VALUES(?,?,?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), worst.get("scenario"), worst.get("portfolio_loss_pct"), payload["portfolio_var_cvar"].get("var_95_pct"), payload["portfolio_var_cvar"].get("cvar_95_pct"), payload["monte_carlo"].get("p95_max_dd_pct"), payload["risk_heatmap"].get("overall_level"), json.dumps(payload, ensure_ascii=False, default=str), V170_VERSION))
        conn.commit(); conn.close()
    except Exception:
        pass
    return payload

def build_v170_text() -> str:
    p = build_v170_payload()
    heat = p["risk_heatmap"]
    worst = p["scenarios"].get("worst_case", {})
    mc = p["monte_carlo"]
    var = p["portfolio_var_cvar"]
    tail = p["tail_risk"]
    liq = p["liquidity_risk"]
    rec = p["drawdown_recovery"]
    lines = [
        "🔥 V170 ADVANCED RISK & STRESS TESTING",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        f"Overall Risk: {heat.get('overall_level')} | Score {heat.get('overall_score')}",
        "",
        "WORST SCENARIO",
        f"{worst.get('scenario')} | Loss {worst.get('portfolio_loss_pct')}% | {worst.get('risk_level')}",
        "",
        "MONTE CARLO",
        f"VaR95: {mc.get('var_95_pct')}% | CVaR95: {mc.get('cvar_95_pct')}% | P95 MaxDD: {mc.get('p95_max_dd_pct')}%",
        "",
        "PORTFOLIO RISK",
        f"Vol: {var.get('portfolio_vol_pct')}% | VaR95: {var.get('var_95_pct')}% | CVaR95: {var.get('cvar_95_pct')}% | Level {var.get('risk_level')}",
        "",
        "TAIL / LIQUIDITY",
        f"Tail: {tail.get('level')} ({tail.get('reasons')}) | Liquidity: {liq.get('level')} score {liq.get('liquidity_score')}",
        "",
        "RECOVERY",
        f"DD {rec.get('drawdown_pct')}% needs +{rec.get('needed_gain_to_recover_pct')}% | ~{rec.get('estimated_months_to_recover')} months",
        "",
        "Quick: /v170/risk-center-json | /v170/scenarios | /v170/monte-carlo | /v170/correlation",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
