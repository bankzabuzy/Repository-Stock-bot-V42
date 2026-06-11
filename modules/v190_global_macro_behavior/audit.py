
from __future__ import annotations
import re
from pathlib import Path
from .common import V190_VERSION

def v190_audit():
    root = Path(__file__).resolve().parents[2]
    routes = {}
    imports = []
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in re.finditer(r'@(?:\w+\.)?route\("([^"]+)"', txt):
            routes.setdefault(m.group(1), []).append(str(p.relative_to(root)))
        if "v190_" in str(p):
            imports.append(str(p.relative_to(root)))
    collisions = {r:f for r,f in routes.items() if len(f)>1}
    return {"ok": True, "version": V190_VERSION, "route_count": len(routes), "route_collision_count": len(collisions), "collisions": collisions, "v190_files": imports}
