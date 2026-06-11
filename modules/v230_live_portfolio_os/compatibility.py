
from __future__ import annotations
import re, importlib, json
from pathlib import Path
from datetime import datetime, timezone
from .common import init_db, connect, V230_VERSION

REQUIRED = [
    "modules.v220_broker_execution_network.dashboard",
    "modules.v210_multi_agent_fund_intelligence.dashboard",
    "modules.v200_autonomous_retail_fund.dashboard",
    "modules.v190_global_macro_behavior.dashboard",
]

def import_audit():
    items=[]
    for m in REQUIRED:
        try:
            importlib.import_module(m); items.append({"module":m,"ok":True})
        except Exception as e:
            items.append({"module":m,"ok":False,"error":str(e)})
    return {"ok": all(i["ok"] for i in items), "items": items}

def route_audit():
    root = Path(__file__).resolve().parents[2]
    routes={}
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts: continue
        try: txt=p.read_text(encoding="utf-8", errors="ignore")
        except Exception: continue
        for m in re.finditer(r'@(?:\w+\.)?route\("([^"]+)"', txt):
            routes.setdefault(m.group(1), []).append(str(p.relative_to(root)))
    collisions={r:f for r,f in routes.items() if len(f)>1}
    return {"route_count": len(routes), "collision_count": len(collisions), "collisions": collisions}

def compatibility_report(compile_ok=True):
    init_db()
    imports=import_audit(); routes=route_audit()
    report={"ok": imports["ok"], "version": V230_VERSION, "compile_ok": compile_ok, "imports": imports, "routes": routes}
    try:
        conn=connect(); cur=conn.cursor()
        cur.execute("INSERT INTO v230_ops_audit(created_at,latest_version,compile_ok,route_collision_count,compatibility_ok,report) VALUES(?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), V230_VERSION, 1 if compile_ok else 0, routes["collision_count"], 1 if imports["ok"] else 0, json.dumps(report, ensure_ascii=False, default=str)))
        conn.commit(); conn.close()
    except Exception: pass
    return report
