
from __future__ import annotations
import re, json, importlib
from pathlib import Path
from datetime import datetime, timezone
from .common import init_db, connect, now_th, V390_VERSION
from .execution_verification import execution_verification_status
from .attribution_engine import attribution_report
from .position_sizing_ai import position_sizing
from .capital_protection import capital_protection

REQUIRED = [
    "modules.v350_production_proof_governance.production_control",
    "modules.v300_institutional_control_center.control_center",
]

def compatibility_audit(compile_ok=True):
    imports = []
    for m in REQUIRED:
        try:
            importlib.import_module(m)
            imports.append({"module": m, "ok": True})
        except Exception as e:
            imports.append({"module": m, "ok": False, "error": str(e)})
    root = Path(__file__).resolve().parents[2]
    routes = {}
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for mm in re.finditer(r'@(?:\w+\.)?route\("([^"]+)"', txt):
            routes.setdefault(mm.group(1), []).append(str(p.relative_to(root)))
    collisions = {r:f for r,f in routes.items() if len(f)>1}
    return {"ok": all(i["ok"] for i in imports), "compile_ok": compile_ok, "imports": imports, "route_count": len(routes), "route_collision_count": len(collisions), "collisions": collisions}

def phase1_center(symbol="SPY"):
    init_db()
    exe = execution_verification_status()
    attr = attribution_report()
    sizing = position_sizing(symbol)
    protect = capital_protection(drawdown=6, losing_days=1, profit_factor=1.25, volatility_level="NORMAL")
    comp = compatibility_audit(True)
    scores = {
        "execution": 85 if exe.get("ok") else 50,
        "attribution": 80 if attr.get("ok") else 50,
        "sizing": 85 if sizing.get("ok") else 50,
        "capital_protection": 90 if protect.get("ok") else 50,
        "compatibility": 85 if comp.get("ok") else 55,
    }
    score = round(sum(scores.values())/len(scores), 2)
    payload = {"ok": True, "version": V390_VERSION, "time_th": now_th(), "symbol": symbol, "phase1_score": score, "scores": scores, "execution_verification": exe, "attribution": attr, "position_sizing": sizing, "capital_protection": protect, "compatibility": comp}
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v390_phase1_audit(created_at,latest_version,compile_ok,route_collision_count,compatibility_ok,phase1_score,report) VALUES(?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), V390_VERSION, 1, comp.get("route_collision_count", 0), 1 if comp.get("ok") else 0, score, json.dumps(payload, ensure_ascii=False, default=str)))
        conn.commit(); conn.close()
    except Exception:
        pass
    return payload

def phase1_text(symbol="SPY"):
    p = phase1_center(symbol)
    lines = [
        "🧱 V390 PHASE 1 EXECUTION / ATTRIBUTION / RISK",
        f"เวลาไทย: {p.get('time_th')}",
        f"Symbol: {symbol}",
        f"Phase1 Score: {p.get('phase1_score')}",
        "",
        "SCORES",
    ]
    lines += [f"- {k}: {v}" for k,v in p.get("scores", {}).items()]
    lines += [
        "",
        "EXECUTION VERIFICATION",
        f"Status: {p.get('execution_verification',{}).get('latest_sample',{}).get('status')} | Slippage: {p.get('execution_verification',{}).get('latest_sample',{}).get('slippage')}",
        "",
        "ATTRIBUTION",
        f"Total R: {p.get('attribution',{}).get('total_r')} | Warmup: {p.get('attribution',{}).get('warmup_mode')}",
        "",
        "POSITION SIZING",
        f"Risk: {p.get('position_sizing',{}).get('suggested_risk_pct')}% | Qty: {p.get('position_sizing',{}).get('suggested_qty')}",
        "",
        "CAPITAL PROTECTION",
        f"Action: {p.get('capital_protection',{}).get('action')} | Multiplier: {p.get('capital_protection',{}).get('risk_multiplier')} | Triggers: {p.get('capital_protection',{}).get('triggers')}",
        "",
        f"Compatibility Routes: {p.get('compatibility',{}).get('route_count')} | Collisions: {p.get('compatibility',{}).get('route_collision_count')}",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
