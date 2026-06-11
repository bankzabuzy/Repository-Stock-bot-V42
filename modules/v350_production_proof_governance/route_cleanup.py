
from __future__ import annotations
import re
from pathlib import Path
from datetime import datetime, timezone
from .common import init_db, connect
def scan_routes():
    root=Path(__file__).resolve().parents[2]; routes={}
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts: continue
        try: txt=p.read_text(encoding="utf-8",errors="ignore")
        except Exception: continue
        for m in re.finditer(r'@(?:\w+\.)?route\("([^"]+)"',txt):
            routes.setdefault(m.group(1),[]).append(str(p.relative_to(root)))
    collisions={r:f for r,f in routes.items() if len(f)>1}
    return {"ok":True,"route_count":len(routes),"collision_count":len(collisions),"collisions":collisions,"routes":routes}
def route_cleanup_registry():
    init_db(); s=scan_routes(); conn=connect(); cur=conn.cursor()
    for route,files in s["routes"].items():
        cur.execute("INSERT OR REPLACE INTO v350_route_registry(route,file,status,collision_count,updated_at) VALUES(?,?,?,?,?)",(route,",".join(files),"COLLISION" if len(files)>1 else "OK",len(files),datetime.now(timezone.utc).isoformat()))
    conn.commit(); conn.close()
    s["cleanup_mode"]="NON_DESTRUCTIVE_REGISTRY"
    return s
