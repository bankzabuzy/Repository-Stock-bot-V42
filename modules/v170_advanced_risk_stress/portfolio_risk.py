
from __future__ import annotations
import math
from typing import Dict, Any, List
from .common import default_positions

CORR = {
    ("US_EQUITY","TACTICAL"): 0.75,
    ("US_EQUITY","CRYPTO"): 0.55,
    ("US_EQUITY","GOLD"): -0.10,
    ("GOLD","CRYPTO"): 0.05,
    ("CASH","US_EQUITY"): 0.0,
    ("CASH","GOLD"): 0.0,
    ("CASH","CRYPTO"): 0.0,
    ("CASH","TACTICAL"): 0.0,
}
VOL = {"US_EQUITY": 18, "GOLD": 16, "CRYPTO": 55, "TACTICAL": 25, "CASH": 1}

def corr(a: str, b: str) -> float:
    if a == b:
        return 1.0
    return CORR.get((a,b), CORR.get((b,a), 0.25))

def portfolio_var_cvar(positions: List[Dict[str, Any]] | None=None) -> Dict[str, Any]:
    positions = positions or default_positions()
    weights = [(p["asset"], float(p["weight"])/100) for p in positions]
    variance = 0.0
    for a, wa in weights:
        for b, wb in weights:
            variance += wa * wb * (VOL.get(a, 20)/100) * (VOL.get(b, 20)/100) * corr(a,b)
    vol = math.sqrt(max(0, variance)) * 100
    var95 = -1.65 * vol
    cvar95 = -2.06 * vol
    concentration = max((p.get("weight",0) for p in positions), default=0)
    risk_level = "CRITICAL" if vol > 35 or concentration > 50 else "HIGH" if vol > 25 or concentration > 35 else "MEDIUM" if vol > 15 else "LOW"
    return {
        "ok": True,
        "portfolio_vol_pct": round(vol, 2),
        "var_95_pct": round(var95, 2),
        "cvar_95_pct": round(cvar95, 2),
        "max_concentration_pct": concentration,
        "risk_level": risk_level,
        "positions": positions,
    }

def correlation_matrix() -> Dict[str, Any]:
    assets = ["US_EQUITY","GOLD","CRYPTO","TACTICAL","CASH"]
    matrix = {a: {b: corr(a,b) for b in assets} for a in assets}
    return {"ok": True, "assets": assets, "matrix": matrix}
