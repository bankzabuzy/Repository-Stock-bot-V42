
from __future__ import annotations
import json, importlib, re
from pathlib import Path
from datetime import datetime, timezone
from .common import init_db, connect, now_th, V500_VERSION
from .shadow_real_money import shadow_real_money
from .autonomous_governance import governance_status

REQUIRED = [
    "modules.v470_phase3_meta_selfheal_dashboard.dashboard",
    "modules.v430_phase2_market_intelligence.dashboard",
    "modules.v390_phase1_execution_attribution_risk.dashboard",
    "modules.v350_production_proof_governance.production_control",
]

def compatibility_audit():
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
    return {"ok": all(i["ok"] for i in imports), "imports": imports, "route_count": len(routes), "route_collision_count": len(collisions), "collisions": collisions}

def _safe_call(path, default):
    try:
        mod, fn = path.rsplit(".", 1)
        m = __import__(mod, fromlist=[fn])
        return getattr(m, fn)()
    except Exception as e:
        return {**default, "error": str(e)}

def arfos_status(symbol="SPY"):
    init_db()
    shadow = shadow_real_money(symbol)
    gov = governance_status()
    comp = compatibility_audit()

    v470 = _safe_call("modules.v470_phase3_meta_selfheal_dashboard.dashboard.phase3_center", {"ok": False})
    v430 = _safe_call("modules.v430_phase2_market_intelligence.dashboard.phase2_center", {"ok": False})
    v390 = _safe_call("modules.v390_phase1_execution_attribution_risk.dashboard.phase1_center", {"ok": False})
    v350 = _safe_call("modules.v350_production_proof_governance.production_control.production_center", {"ok": False})

    scores = {
        "v350_production_proof": 85 if v350.get("ok") else 50,
        "v390_phase1": 85 if v390.get("ok") else 50,
        "v430_phase2": 85 if v430.get("ok") else 50,
        "v470_phase3": 85 if v470.get("ok") else 50,
        "v480_shadow": 85 if shadow.get("ok") else 50,
        "v490_governance": 85 if gov.get("ok") else 50,
        "compatibility": 85 if comp.get("ok") else 55,
    }
    readiness = round(sum(scores.values()) / len(scores), 2)
    live_allowed = 1 if gov.get("decision") == "LIVE_READY_REQUIRES_FINAL_HUMAN_APPROVAL" else 0
    paper_allowed = 1
    broker_allowed = 1 if gov.get("broker_verified") else 0
    decision = "ARFOS_PAPER_READY" if readiness >= 80 else "ARFOS_NEEDS_REVIEW"
    if live_allowed:
        decision = "ARFOS_LIVE_READY_REQUIRES_HUMAN_APPROVAL"

    payload = {
        "ok": True,
        "version": V500_VERSION,
        "time_th": now_th(),
        "symbol": symbol,
        "system_mode": "PAPER_FIRST",
        "readiness_score": readiness,
        "decision": decision,
        "scores": scores,
        "shadow_real_money": shadow,
        "governance": gov,
        "compatibility": comp,
        "layers": {"v350": v350, "v390": v390, "v430": v430, "v470": v470},
        "safety_note": "No profit guarantee. Live trading is blocked unless explicit broker verification and human approval are enabled.",
    }
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v500_arfos_core(created_at,system_mode,readiness_score,live_allowed,paper_allowed,broker_allowed,decision,report,model_version) VALUES(?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), "PAPER_FIRST", readiness, live_allowed, paper_allowed, broker_allowed, decision, json.dumps(payload, ensure_ascii=False, default=str), V500_VERSION))
    conn.commit(); conn.close()
    return payload

def arfos_text(symbol="SPY"):
    p = arfos_status(symbol)
    lines = [
        "🏁 V500 ARFOS AUTONOMOUS RETAIL FUND OS",
        f"เวลาไทย: {p.get('time_th')}",
        f"Readiness Score: {p.get('readiness_score')} | Decision: {p.get('decision')}",
        "",
        "LAYER SCORES",
    ]
    lines += [f"- {k}: {v}" for k, v in p.get("scores", {}).items()]
    lines += [
        "",
        "SHADOW REAL MONEY",
        f"AI: {p.get('shadow_real_money',{}).get('ai_decision')} | Human: {p.get('shadow_real_money',{}).get('human_decision')} | Divergence: {p.get('shadow_real_money',{}).get('divergence_score')}",
        "",
        "GOVERNANCE",
        f"Decision: {p.get('governance',{}).get('decision')} | Broker Verified: {p.get('governance',{}).get('broker_verified')}",
        "",
        f"Compatibility Routes: {p.get('compatibility',{}).get('route_count')} | Collisions: {p.get('compatibility',{}).get('route_collision_count')}",
        "",
        "Safety: Paper-first. ไม่รับประกันกำไร และห้าม Live หากยังไม่ผ่าน broker validation + human approval",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
