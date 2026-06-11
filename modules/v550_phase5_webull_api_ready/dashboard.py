
from __future__ import annotations
import re, importlib, json
from pathlib import Path
from datetime import datetime, timezone
from .common import init_db, connect, now_th, V550_VERSION
from .broker_integration import broker_integration_status
from .secret_manager import secret_manager_status
from .order_dryrun import order_dry_run
from .human_approval import create_approval, approval_center_status
from .api_health_center import api_health_center
from .safety_center import safety_center_status

REQUIRED = [
    "modules.v500_arfos_autonomous_retail_fund_os.dashboard",
    "modules.v470_phase3_meta_selfheal_dashboard.dashboard",
    "modules.v430_phase2_market_intelligence.dashboard",
    "modules.v390_phase1_execution_attribution_risk.dashboard",
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

def phase5_center(symbol="SPY"):
    init_db()
    secrets = secret_manager_status()
    brokers = broker_integration_status()
    dry = order_dry_run(symbol, "BUY", 1, "WEBULL")
    approval = create_approval(symbol, "BUY", 1, "WEBULL", "SAFE")
    approvals = approval_center_status()
    api = api_health_center()
    safety = safety_center_status()
    comp = compatibility_audit(True)

    scores = {
        "secret_manager": 90 if secrets.get("ok") else 50,
        "webull_config": 90 if brokers.get("webull_configured") else 65,
        "dry_run": 90 if dry.get("status") == "PASS_DRY_RUN" else 55,
        "human_approval": 90 if approval.get("ok") else 55,
        "api_health": 85 if api.get("ok") else 50,
        "safety": safety.get("safety_score", 60),
        "compatibility": 85 if comp.get("ok") else 55,
    }
    score = round(sum(scores.values()) / len(scores), 2)
    decision = "WEBULL_READY_AFTER_API_APPROVAL_AND_ENV" if brokers.get("webull_configured") else "WAIT_WEBULL_API_KEYS"
    payload = {
        "ok": True,
        "version": V550_VERSION,
        "time_th": now_th(),
        "symbol": symbol,
        "phase5_score": score,
        "decision": decision,
        "scores": scores,
        "secrets": secrets,
        "brokers": brokers,
        "dry_run": dry,
        "approval": approval,
        "approval_center": approvals,
        "api_health": api,
        "safety": safety,
        "compatibility": comp,
    }
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v550_phase5_audit(created_at,latest_version,compile_ok,route_collision_count,compatibility_ok,phase5_score,report) VALUES(?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), V550_VERSION, 1, comp.get("route_collision_count", 0), 1 if comp.get("ok") else 0, score, json.dumps(payload, ensure_ascii=False, default=str)))
        conn.commit(); conn.close()
    except Exception:
        pass
    return payload

def phase5_text(symbol="SPY"):
    p = phase5_center(symbol)
    webull = next((b for b in p.get("brokers",{}).get("brokers",[]) if b.get("broker")=="WEBULL"), {})
    lines = [
        "🔐 V550 PHASE 5 WEBULL API READY SAFE EXECUTION",
        f"เวลาไทย: {p.get('time_th')}",
        f"Phase5 Score: {p.get('phase5_score')} | Decision: {p.get('decision')}",
        "",
        "SCORES",
    ]
    lines += [f"- {k}: {v}" for k,v in p.get("scores", {}).items()]
    lines += [
        "",
        "WEBULL",
        f"Configured: {webull.get('configured')} | Status: {webull.get('status')} | Safe Mode: {webull.get('safe_mode')}",
        "",
        "DRY RUN",
        f"Status: {p.get('dry_run',{}).get('status')} | Notional: {p.get('dry_run',{}).get('notional')} | Slippage: {p.get('dry_run',{}).get('estimated_slippage')}",
        "",
        "HUMAN APPROVAL",
        f"Approval: {p.get('approval',{}).get('approval_id')} | Status: {p.get('approval',{}).get('status')}",
        "",
        "API HEALTH / SAFETY",
        f"Webull API: {p.get('api_health',{}).get('webull_status',{}).get('status')} | Safety Score: {p.get('safety',{}).get('safety_score')}",
        "",
        f"Compatibility Routes: {p.get('compatibility',{}).get('route_count')} | Collisions: {p.get('compatibility',{}).get('route_collision_count')}",
        "",
        "Safety: ยังไม่ส่งคำสั่งจริง จนกว่า Webull อนุมัติ API + ตั้งค่า .env + Human Approval",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
