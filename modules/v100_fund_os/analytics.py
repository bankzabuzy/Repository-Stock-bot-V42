
from __future__ import annotations
from typing import Dict, Any, List
import math

def fund_metrics(returns: List[float] | None = None) -> Dict[str, Any]:
    returns = returns or []
    if not returns:
        returns = [0.8,-0.4,1.1,-0.5,0.6,1.4,-0.7,0.9]
    mean = sum(returns)/len(returns)
    std = math.sqrt(sum((r-mean)**2 for r in returns)/max(1,len(returns)-1))
    downside = [min(0,r) for r in returns]
    down_std = math.sqrt(sum(r*r for r in downside)/max(1,len(downside)))
    sharpe = mean/std*math.sqrt(252) if std else None
    sortino = mean/down_std*math.sqrt(252) if down_std else None
    equity=0; peak=0; dd=0
    for r in returns:
        equity += r
        peak = max(peak,equity)
        dd = max(dd, peak-equity)
    calmar = (mean*252)/dd if dd else None
    return {"ok": True, "sharpe": round(sharpe,2) if sharpe else None, "sortino": round(sortino,2) if sortino else None, "calmar": round(calmar,2) if calmar else None, "rolling_max_dd_r": round(dd,2), "sample_returns": len(returns)}
