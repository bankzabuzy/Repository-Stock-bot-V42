
from __future__ import annotations
import re
from pathlib import Path
from .common import V200_VERSION

def v200_audit():
    root = Path(__file__).resolve().parents[2]
    routes = {}
    vfiles = []
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "v200_" in str(p):
            vfiles.append(str(p.relative_to(root)))
        for m in re.finditer(r'@(?:\w+\.)?route\("([^"]+)"', txt):
            routes.setdefault(m.group(1), []).append(str(p.relative_to(root)))
    collisions = {r:f for r,f in routes.items() if len(f)>1}
    return {"ok": True, "version": V200_VERSION, "route_count": len(routes), "route_collision_count": len(collisions), "collisions": collisions, "v200_files": vfiles}
