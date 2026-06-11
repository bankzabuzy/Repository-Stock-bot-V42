
from __future__ import annotations
from typing import Dict, Any, List
from .config import get_config
SECTOR_MAP = {"NVDA":"Technology","AAPL":"Technology","MSFT":"Technology","AMD":"Technology","TSM":"Semiconductors","QQQ":"ETF","SPY":"ETF","GOLD":"Gold","THAI_GOLD":"Gold"}

def portfolio_heat(positions: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    if positions is None:
        import os
        raw = os.getenv("V100_POSITIONS", "NVDA:8,TSM:6,QQQ:12,THAI_GOLD:10")
        positions = []
        for p in raw.split(","):
            if ":" in p:
                s,w = p.split(":",1)
                positions.append({"symbol":s.strip().upper(),"weight_pct":float(w)})
    cfg = get_config()
    heat = sum(abs(float(p.get("weight_pct",0))) for p in positions)
    sectors = {}
    for p in positions:
        sym = p.get("symbol","").upper()
        sec = SECTOR_MAP.get(sym,"Other")
        sectors[sec] = sectors.get(sec,0)+float(p.get("weight_pct",0))
    return {"ok": True, "positions": positions, "portfolio_heat_pct": round(heat,2), "max_heat_pct": cfg.max_portfolio_heat_pct, "sector_exposure": sectors, "decision": "NO_NEW_POSITION" if heat > cfg.max_portfolio_heat_pct else "ALLOW"}
