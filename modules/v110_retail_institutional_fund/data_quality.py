
from __future__ import annotations
import os
from typing import Dict, Any, List
from .common import get_yfinance_price

def check_data_sources(symbols: List[str] | None=None) -> Dict[str, Any]:
    symbols = symbols or ["SPY", "QQQ", "NVDA", "TSM", "GC=F"]
    results = []
    for s in symbols:
        r = get_yfinance_price(s)
        issues = []
        if not r.get("ok"):
            issues.append(r.get("error") or "no_price")
        if r.get("price") is not None and r.get("previous_close"):
            jump = abs((r["price"] - r["previous_close"]) / r["previous_close"] * 100)
            if jump > float(os.getenv("V110_MAX_PRICE_JUMP_PCT", "25")):
                issues.append(f"abnormal_jump_{round(jump,2)}pct")
        results.append({**r, "issues": issues, "quality": "PASS" if not issues else "FAIL"})
    return {
        "ok": all(x.get("quality") == "PASS" for x in results),
        "sources": {"Yahoo Finance": any(x.get("ok") for x in results)},
        "items": results,
        "decision": "ALLOW_SIGNALS" if all(x.get("quality") == "PASS" for x in results) else "HOLD_BAD_DATA",
    }
