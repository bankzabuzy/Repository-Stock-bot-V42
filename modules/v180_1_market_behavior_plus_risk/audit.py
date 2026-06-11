
from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, Any
from .common import V180_1_VERSION

def route_collision_audit() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    routes = {}
    collisions = {}
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in re.finditer(r'@(?:\w+\.)?route\("([^"]+)"', txt):
            route = m.group(1)
            routes.setdefault(route, []).append(str(p.relative_to(root)))
    for route, files in routes.items():
        if len(files) > 1:
            collisions[route] = files
    return {
        "ok": len(collisions) == 0,
        "version": V180_1_VERSION,
        "route_count": len(routes),
        "collision_count": len(collisions),
        "collisions": collisions,
        "note": "ถ้ามี collision แปลว่า route เดียวกันถูกประกาศซ้ำ อาจทำให้ Flask endpoint ชน",
    }

def version_latest_audit() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    refs = set()
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        refs.update(re.findall(r"V\d+(?:\.\d+)?[A-Z0-9_\.]*", txt))
    return {
        "ok": True,
        "latest": V180_1_VERSION,
        "versions_found_count": len(refs),
        "versions_sample": sorted(refs)[-30:],
        "note": "Legacy versions are intentionally kept for backward compatibility; latest control layer is V180.1",
    }

def full_audit() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": V180_1_VERSION,
        "route_audit": route_collision_audit(),
        "version_audit": version_latest_audit(),
    }
