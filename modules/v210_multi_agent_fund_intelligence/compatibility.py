
from __future__ import annotations
import re, importlib, json
from pathlib import Path
from datetime import datetime, timezone
from .common import init_db, connect, V210_VERSION

REQUIRED_MODULES = [
    "modules.v200_autonomous_retail_fund.dashboard",
    "modules.v190_global_macro_behavior.dashboard",
    "modules.v180_1_market_behavior_plus_risk.forecast_plus_risk",
    "modules.v170_advanced_risk_stress.risk_dashboard",
]

def import_audit() -> dict:
    items = []
    for m in REQUIRED_MODULES:
        try:
            importlib.import_module(m)
            items.append({"module": m, "ok": True})
        except Exception as e:
            items.append({"module": m, "ok": False, "error": str(e)})
    return {"ok": all(i.get("ok") for i in items), "items": items}

def route_collision_audit() -> dict:
    root = Path(__file__).resolve().parents[2]
    routes = {}
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in re.finditer(r'@(?:\w+\.)?route\("([^"]+)"', txt):
            routes.setdefault(m.group(1), []).append(str(p.relative_to(root)))
    collisions = {r:f for r,f in routes.items() if len(f)>1}
    return {"ok": True, "route_count": len(routes), "collision_count": len(collisions), "collisions": collisions}

def compatibility_report(compile_ok: bool=True) -> dict:
    init_db()
    imports = import_audit()
    routes = route_collision_audit()
    report = {
        "ok": imports.get("ok"),
        "version": V210_VERSION,
        "compile_ok": compile_ok,
        "imports": imports,
        "routes": routes,
        "backward_compatibility": "V170/V180.1/V190/V200 retained; V210 adds multi-agent committee layer",
    }
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v210_compatibility_audit(created_at,latest_version,compile_ok,route_collision_count,required_modules_ok,report) VALUES(?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), V210_VERSION, 1 if compile_ok else 0, routes.get("collision_count"), 1 if imports.get("ok") else 0, json.dumps(report, ensure_ascii=False, default=str)))
        conn.commit(); conn.close()
    except Exception:
        pass
    return report
