
from __future__ import annotations
import re, importlib, json
from pathlib import Path
from datetime import datetime, timezone
from .common import init_db, connect, now_th, V470_VERSION
from .meta_learning import meta_learning_weights
from .self_healing import self_healing_check
from .explainable_fund_report import explainable_fund_report
from .investor_dashboard import investor_dashboard

REQUIRED = [
    "modules.v430_phase2_market_intelligence.dashboard",
    "modules.v390_phase1_execution_attribution_risk.dashboard",
    "modules.v350_production_proof_governance.production_control",
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

def phase3_center(symbol="SPY"):
    init_db()
    meta = meta_learning_weights()
    heal = self_healing_check()
    explain = explainable_fund_report(symbol)
    investor = investor_dashboard()
    comp = compatibility_audit(True)
    scores = {
        "meta_learning": 85 if meta.get("ok") else 50,
        "self_healing": 80 if heal.get("ok") else 50,
        "explainability": 85 if explain.get("ok") else 50,
        "investor_dashboard": 85 if investor.get("ok") else 50,
        "compatibility": 85 if comp.get("ok") else 55,
    }
    score = round(sum(scores.values())/len(scores), 2)
    payload = {"ok": True, "version": V470_VERSION, "time_th": now_th(), "symbol": symbol, "phase3_score": score, "scores": scores, "meta_learning": meta, "self_healing": heal, "explainable_report": explain, "investor_dashboard": investor, "compatibility": comp}
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v470_phase3_audit(created_at,latest_version,compile_ok,route_collision_count,compatibility_ok,phase3_score,report) VALUES(?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), V470_VERSION, 1, comp.get("route_collision_count",0), 1 if comp.get("ok") else 0, score, json.dumps(payload, ensure_ascii=False, default=str)))
        conn.commit(); conn.close()
    except Exception:
        pass
    return payload

def phase3_text(symbol="SPY"):
    p = phase3_center(symbol)
    inv = p.get("investor_dashboard", {})
    exp = p.get("explainable_report", {})
    lines = [
        "🧬 V470 PHASE 3 META / SELF-HEAL / REPORT / DASHBOARD",
        f"เวลาไทย: {p.get('time_th')}",
        f"Symbol: {symbol}",
        f"Phase3 Score: {p.get('phase3_score')}",
        "",
        "META LEARNING",
        f"Decision: {p.get('meta_learning',{}).get('decision')} | Models: {len(p.get('meta_learning',{}).get('weights', []))}",
        "",
        "SELF HEALING",
        f"Status: {p.get('self_healing',{}).get('overall_status')} | Events: {len(p.get('self_healing',{}).get('events', []))}",
        "",
        "EXPLAINABLE FUND REPORT",
        f"Decision: {exp.get('decision')} | Why Wait: {exp.get('why_wait')}",
        "",
        "INVESTOR DASHBOARD",
        f"NAV: {inv.get('nav')} | PF: {inv.get('profit_factor')} | Sharpe: {inv.get('sharpe')} | DD: {inv.get('drawdown')} | Warmup: {inv.get('warmup_mode')}",
        "",
        f"Compatibility Routes: {p.get('compatibility',{}).get('route_count')} | Collisions: {p.get('compatibility',{}).get('route_collision_count')}",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
