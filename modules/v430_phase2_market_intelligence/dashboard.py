
from __future__ import annotations
import re, importlib, json
from pathlib import Path
from datetime import datetime, timezone
from .common import init_db, connect, now_th, V430_VERSION
from .microstructure_ai import market_microstructure
from .regime_ai import regime_ai
from .multi_agent_debate import multi_agent_debate
from .digital_twin import digital_twin_gate

REQUIRED = [
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

def phase2_center(symbol="SPY"):
    init_db()
    micro = market_microstructure(symbol)
    regime = regime_ai(symbol)
    debate = multi_agent_debate(symbol)
    twin = digital_twin_gate(symbol)
    comp = compatibility_audit(True)
    scores = {
        "microstructure": 85 if micro.get("ok") else 50,
        "regime": 85 if regime.get("ok") else 50,
        "debate": 85 if debate.get("ok") else 50,
        "digital_twin": 80 if twin.get("ok") else 50,
        "compatibility": 85 if comp.get("ok") else 55,
    }
    score = round(sum(scores.values())/len(scores), 2)
    payload = {"ok": True, "version": V430_VERSION, "time_th": now_th(), "symbol": symbol, "phase2_score": score, "scores": scores, "microstructure": micro, "regime": regime, "debate": debate, "digital_twin": twin, "compatibility": comp}
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v430_phase2_audit(created_at,latest_version,compile_ok,route_collision_count,compatibility_ok,phase2_score,report) VALUES(?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), V430_VERSION, 1, comp.get("route_collision_count", 0), 1 if comp.get("ok") else 0, score, json.dumps(payload, ensure_ascii=False, default=str)))
        conn.commit(); conn.close()
    except Exception:
        pass
    return payload

def phase2_text(symbol="SPY"):
    p = phase2_center(symbol)
    lines = [
        "🧠 V430 PHASE 2 MARKET INTELLIGENCE",
        f"เวลาไทย: {p.get('time_th')}",
        f"Symbol: {symbol}",
        f"Phase2 Score: {p.get('phase2_score')}",
        "",
        "MICROSTRUCTURE",
        f"Liquidity: {p.get('microstructure',{}).get('liquidity_score')} | Flow: {p.get('microstructure',{}).get('order_flow_bias')} | StopHunt: {p.get('microstructure',{}).get('stop_hunt_score')}",
        "",
        "REGIME",
        f"{p.get('regime',{}).get('regime')} → {p.get('regime',{}).get('strategy_mapping')} | Confidence {p.get('regime',{}).get('confidence')}",
        "",
        "MULTI-AGENT DEBATE",
        f"Decision: {p.get('debate',{}).get('final_decision')} | Consensus: {p.get('debate',{}).get('consensus_score')}% | Penalty: {p.get('debate',{}).get('confidence_penalty')}",
        "",
        "DIGITAL TWIN",
        f"Safety Gate: {p.get('digital_twin',{}).get('decision')} | Failed: {len(p.get('digital_twin',{}).get('failed', []))}",
        "",
        f"Compatibility Routes: {p.get('compatibility',{}).get('route_count')} | Collisions: {p.get('compatibility',{}).get('route_collision_count')}",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
