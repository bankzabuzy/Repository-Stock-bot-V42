
from __future__ import annotations
import os
from typing import Dict, Any

SECTOR = {"NVDA":"Tech","AAPL":"Tech","MSFT":"Tech","AMD":"Tech","TSM":"Semi","QQQ":"ETF","SPY":"ETF","THAI_GOLD":"Gold","GOLD":"Gold","GC=F":"Gold"}

def exposure_control() -> Dict[str, Any]:
    raw = os.getenv("V110_POSITIONS", os.getenv("V100_POSITIONS", "NVDA:8,TSM:6,QQQ:12,THAI_GOLD:10,CASH:20"))
    positions = []
    for p in raw.split(","):
        if ":" in p:
            s, w = p.split(":", 1)
            try:
                weight = float(w)
            except Exception:
                weight = 0
            positions.append({"symbol": s.strip().upper(), "weight_pct": weight})
    max_symbol = float(os.getenv("V110_MAX_SYMBOL_WEIGHT", "15"))
    max_sector = float(os.getenv("V110_MAX_SECTOR_WEIGHT", "40"))
    min_cash = float(os.getenv("V110_MIN_CASH_WEIGHT", "10"))
    sectors = {}
    breaches = []
    cash = 0
    for p in positions:
        sym = p["symbol"]
        w = p["weight_pct"]
        if sym == "CASH":
            cash += w
        if abs(w) > max_symbol and sym != "CASH":
            breaches.append(f"{sym}_over_symbol_limit")
        sec = SECTOR.get(sym, "Other")
        sectors[sec] = sectors.get(sec, 0) + w
    for sec, w in sectors.items():
        if sec != "Other" and abs(w) > max_sector:
            breaches.append(f"{sec}_over_sector_limit")
    if cash < min_cash:
        breaches.append("cash_below_min")
    return {
        "ok": not breaches,
        "positions": positions,
        "sector_exposure": sectors,
        "cash_pct": cash,
        "breaches": breaches,
        "decision": "ALLOW" if not breaches else "REDUCE_RISK",
    }
