
from __future__ import annotations
import random, math, os
from typing import Dict, Any, List
from .common import percentile

def monte_carlo_stress(trials: int=5000, days: int=252, annual_return: float=0.10, annual_vol: float=0.18) -> Dict[str, Any]:
    trials = min(max(int(trials), 500), 20000)
    days = min(max(int(days), 30), 756)
    random.seed(170)
    daily_mu = annual_return / 252
    daily_sigma = annual_vol / (252 ** 0.5)
    finals, maxdds = [], []
    for _ in range(trials):
        equity = 1.0
        peak = 1.0
        dd = 0.0
        for _d in range(days):
            r = random.gauss(daily_mu, daily_sigma)
            equity *= (1 + r)
            peak = max(peak, equity)
            dd = max(dd, (peak-equity)/peak)
        finals.append((equity-1)*100)
        maxdds.append(dd*100)
    var95 = percentile(finals, 0.05)
    tail = [x for x in finals if var95 is not None and x <= var95]
    cvar95 = sum(tail)/len(tail) if tail else var95
    return {
        "ok": True,
        "trials": trials,
        "days": days,
        "expected_return_pct": round(sum(finals)/len(finals), 2),
        "var_95_pct": round(var95, 2) if var95 is not None else None,
        "cvar_95_pct": round(cvar95, 2) if cvar95 is not None else None,
        "median_max_dd_pct": round(percentile(maxdds, 0.5), 2),
        "p95_max_dd_pct": round(percentile(maxdds, 0.95), 2),
        "risk_of_loss_pct": round(sum(1 for x in finals if x < 0)/len(finals)*100, 2),
    }
