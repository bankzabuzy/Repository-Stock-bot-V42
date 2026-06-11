
from __future__ import annotations
from typing import Dict, Any
from .config import V100_VERSION
from .database import init_db
from .monitoring import health
from .market_data import prices
from .ensemble import ensemble_vote
from .portfolio import portfolio_heat
from .execution import approval_gate
from .analytics import fund_metrics
from .research import run_research_experiment

def build_fund_os_payload(symbol: str = "SPY") -> Dict[str, Any]:
    db = init_db()
    px = prices(symbol)
    ens = ensemble_vote(symbol, px.get("prices", [])) if px.get("ok") else {"ok": False, "reason": px.get("reason")}
    gate = approval_gate(ens) if ens.get("ok") else {"ok": False, "decision": "BLOCKED"}
    return {
        "ok": True,
        "version": V100_VERSION,
        "symbol": symbol.upper(),
        "health": health(),
        "market_data": {"ok": px.get("ok"), "last": px.get("last"), "reason": px.get("reason")},
        "ensemble": ens,
        "approval_gate": gate,
        "portfolio": portfolio_heat(),
        "analytics": fund_metrics(),
        "endpoints": ["/v100/fund-os", "/v100/fund-dashboard", "/v100/health", "/v100/research"],
    }

def build_fund_dashboard_text(symbol: str = "SPY") -> str:
    p = build_fund_os_payload(symbol)
    h = p.get("health", {})
    ens = p.get("ensemble", {})
    gate = p.get("approval_gate", {})
    port = p.get("portfolio", {})
    met = p.get("analytics", {})
    lines = [
        "🚀 V100 FUND OPERATING SYSTEM",
        f"Symbol: {p.get('symbol')}",
        "",
        f"Health: {'✅' if h.get('ok') else '❌'} | DB: {h.get('db',{}).get('db')}",
        f"Broker: {h.get('broker',{}).get('default')} | Mode: {h.get('config',{}).get('mode')}",
        "",
        "ENSEMBLE",
        f"Signal: {ens.get('signal')} | Confidence: {ens.get('confidence')} | Votes: {ens.get('votes')}",
        "",
        "APPROVAL GATE",
        f"Decision: {gate.get('decision')} | Checks: {gate.get('checks')}",
        "",
        "PORTFOLIO",
        f"Heat: {port.get('portfolio_heat_pct')}% / Max {port.get('max_heat_pct')}% | Decision: {port.get('decision')}",
        "",
        "FUND ANALYTICS",
        f"Sharpe: {met.get('sharpe')} | Sortino: {met.get('sortino')} | Calmar: {met.get('calmar')} | Rolling DD: {met.get('rolling_max_dd_r')}",
        "",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
