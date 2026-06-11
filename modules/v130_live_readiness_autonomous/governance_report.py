
from __future__ import annotations
from typing import Dict, Any
from .common import now_th, V130_VERSION
from .readiness import run_readiness_checks
from .capital_allocation import allocation_plan
from .autonomous_controls import autonomous_mode_status, generate_rebalance_intents
from .incident_response import incident_summary

def build_v130_payload() -> Dict[str, Any]:
    readiness = run_readiness_checks()
    allocation = allocation_plan()
    auto = autonomous_mode_status()
    incidents = incident_summary()
    return {
        "ok": True,
        "version": V130_VERSION,
        "time_th": now_th(),
        "readiness": readiness,
        "capital_allocation": allocation,
        "autonomous_mode": auto,
        "incident_summary": incidents,
        "endpoints": ["/v130/governance-center", "/v130/governance-json", "/v130/readiness", "/v130/allocation", "/v130/autonomous-rebalance", "/v130/incidents"],
    }

def build_v130_text() -> str:
    p = build_v130_payload()
    r = p["readiness"]
    a = p["capital_allocation"]
    auto = p["autonomous_mode"]
    inc = p["incident_summary"]
    lines = [
        "🏦 V130 LIVE TRADING READINESS & AUTONOMOUS PORTFOLIO CONTROL",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        "READINESS",
        f"Status: {r.get('status')} | Score: {r.get('overall_score')}",
    ]
    for c in r.get("checks", []):
        lines.append(f"- {c.get('name')}: {'✅' if c.get('ok') else '❌'} | {c.get('score')}")
    lines += [
        "",
        "CAPITAL ALLOCATION",
        f"Decision: {a.get('decision')} | Threshold: {a.get('threshold_pct')}%",
    ]
    for item in a.get("items", []):
        lines.append(f"- {item.get('bucket')}: target {item.get('target_weight')}% / current {item.get('current_weight')}% | {item.get('action')}")
    lines += [
        "",
        "AUTONOMOUS MODE",
        f"Mode: {auto.get('mode')} | Enabled: {auto.get('enabled')} | Paper Only: {auto.get('paper_only')}",
        "",
        "INCIDENTS",
        f"Recent: {len(inc.get('items', []))} | Severity: {inc.get('severity_counts')}",
        "",
        "Safety: LIVE trading remains blocked unless ALLOW_LIVE_TRADING=true",
        "Quick: /v130/readiness | /v130/allocation | /v130/autonomous-rebalance",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
