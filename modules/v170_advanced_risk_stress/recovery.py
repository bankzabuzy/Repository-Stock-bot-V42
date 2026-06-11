
from __future__ import annotations
from typing import Dict, Any

def drawdown_recovery_analysis(drawdown_pct: float=-15, monthly_return_pct: float=3) -> Dict[str, Any]:
    dd = abs(float(drawdown_pct))
    m = max(0.1, float(monthly_return_pct))
    needed_gain = (1/(1-dd/100)-1)*100 if dd < 100 else None
    months = needed_gain / m if needed_gain is not None else None
    return {
        "ok": True,
        "drawdown_pct": -dd,
        "needed_gain_to_recover_pct": round(needed_gain,2) if needed_gain is not None else None,
        "assumed_monthly_return_pct": m,
        "estimated_months_to_recover": round(months,1) if months is not None else None,
    }
