
from __future__ import annotations
import re, importlib, json
from pathlib import Path
from .common import V300_VERSION

REQUIRED = [
    "modules.v240_autonomous_fund_manager.dashboard",
    "modules.v230_live_portfolio_os.dashboard",
    "modules.v220_broker_execution_network.dashboard",
    "modules.v210_multi_agent_fund_intelligence.dashboard",
    "modules.v200_autonomous_retail_fund.dashboard",
]

def compatibility_report():
    imports=[]
    for m in REQUIRED:
        try:
            importlib.import_module(m); imports.append({"module":m,"ok":True})
        except Exception as e:
            imports.append({"module":m,"ok":False,"error":str(e)})
    root = Path(__file__).resolve().parents[2]
    routes={}
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts: continue
        try: txt=p.read_text(encoding="utf-8", errors="ignore")
        except Exception: continue
        for mm in re.finditer(r'@(?:\w+\.)?route\("([^"]+)"', txt):
            routes.setdefault(mm.group(1), []).append(str(p.relative_to(root)))
    collisions={r:f for r,f in routes.items() if len(f)>1}
    return {"ok": all(i["ok"] for i in imports), "version": V300_VERSION, "imports": imports, "route_count": len(routes), "route_collision_count": len(collisions), "collisions": collisions}
