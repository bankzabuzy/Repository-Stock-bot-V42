
from __future__ import annotations
from typing import Dict, Any, List
from .common import default_positions

SCENARIOS = {
    "COVID_CRASH": {"US_EQUITY": -32, "GOLD": 3, "CRYPTO": -45, "TACTICAL": -20, "CASH": 0},
    "GFC_2008": {"US_EQUITY": -45, "GOLD": 8, "CRYPTO": -55, "TACTICAL": -25, "CASH": 0},
    "INFLATION_SHOCK": {"US_EQUITY": -18, "GOLD": 12, "CRYPTO": -30, "TACTICAL": -12, "CASH": 0},
    "AI_BUBBLE_BURST": {"US_EQUITY": -28, "GOLD": 5, "CRYPTO": -35, "TACTICAL": -22, "CASH": 0},
    "USD_SPIKE": {"US_EQUITY": -12, "GOLD": -10, "CRYPTO": -20, "TACTICAL": -8, "CASH": 0},
    "RISK_ON_MELTUP": {"US_EQUITY": 18, "GOLD": -3, "CRYPTO": 25, "TACTICAL": 12, "CASH": 0},
}

def scenario_loss(scenario_name: str, positions: List[Dict[str, Any]] | None=None) -> Dict[str, Any]:
    positions = positions or default_positions()
    scen = SCENARIOS.get(scenario_name.upper(), SCENARIOS["COVID_CRASH"])
    contributions = []
    total = 0.0
    for p in positions:
        asset = p.get("asset")
        w = float(p.get("weight", 0))
        shock = float(scen.get(asset, scen.get("TACTICAL", -10)))
        contrib = w/100 * shock
        total += contrib
        contributions.append({"asset": asset, "weight": w, "shock_pct": shock, "contribution_pct": round(contrib, 2)})
    risk_level = "CRITICAL" if total <= -25 else "HIGH" if total <= -15 else "MEDIUM" if total <= -8 else "LOW"
    return {"ok": True, "scenario": scenario_name.upper(), "portfolio_loss_pct": round(total, 2), "risk_level": risk_level, "contributions": contributions}

def run_all_scenarios() -> Dict[str, Any]:
    items = [scenario_loss(name) for name in SCENARIOS.keys()]
    worst = min(items, key=lambda x: x.get("portfolio_loss_pct", 0)) if items else None
    return {"ok": True, "items": items, "worst_case": worst}
