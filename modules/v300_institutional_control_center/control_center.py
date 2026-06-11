
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, V300_VERSION, now_th
from .data_bus import data_bus_status
from .feature_store import feature_store_status
from .model_registry import model_registry_status
from .explainability import explain_decision

def _safe(path, default=None):
    try:
        mod, fn = path.rsplit(".",1)
        m = __import__(mod, fromlist=[fn])
        return getattr(m, fn)()
    except Exception as e:
        return default or {"ok": False, "error": str(e)}

def institutional_control_center(symbol: str="SPY"):
    init_db()
    data = data_bus_status()
    features = feature_store_status()
    registry = model_registry_status()
    explain = explain_decision(symbol, "WAIT")

    v240 = _safe("modules.v240_autonomous_fund_manager.dashboard.build_v240_payload", {"ok": False})
    v230 = _safe("modules.v230_live_portfolio_os.dashboard.build_v230_payload", {"ok": False})
    v220 = _safe("modules.v220_broker_execution_network.dashboard.build_v220_payload", {"ok": False})
    v210 = _safe("modules.v210_multi_agent_fund_intelligence.dashboard.build_v210_payload", {"ok": False})
    v200 = _safe("modules.v200_autonomous_retail_fund.dashboard.build_v200_payload", {"ok": False})

    component_scores = {
        "data_bus": 90 if data.get("ok") else 50,
        "feature_store": 90 if features.get("ok") else 50,
        "model_registry": 90 if registry.get("ok") else 50,
        "explainability": 90 if explain.get("ok") else 50,
        "v240": 90 if v240.get("ok") else 50,
        "v230": 90 if v230.get("ok") else 50,
        "v220": 90 if v220.get("ok") else 50,
        "v210": 90 if v210.get("ok") else 50,
        "v200": 90 if v200.get("ok") else 50,
    }
    system_score = round(sum(component_scores.values())/len(component_scores),2)
    decision = "PRODUCTION_READY_PAPER" if system_score >= 80 else "CHECK_SYSTEM"
    payload = {
        "ok": True,
        "version": V300_VERSION,
        "time_th": now_th(),
        "symbol": symbol,
        "system_score": system_score,
        "decision": decision,
        "component_scores": component_scores,
        "data_bus": data,
        "feature_store": features,
        "model_registry": registry,
        "explainability": explain,
        "legacy_layers": {"v240": v240, "v230": v230, "v220": v220, "v210": v210, "v200": v200},
    }
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v300_control_audit(created_at,latest_version,compile_ok,route_collision_count,compatibility_ok,system_score,report) VALUES(?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), V300_VERSION, 1, 0, 1 if decision=="PRODUCTION_READY_PAPER" else 0, system_score, json.dumps(payload, ensure_ascii=False, default=str)))
        conn.commit(); conn.close()
    except Exception:
        pass
    return payload

def control_center_text(symbol: str="SPY"):
    p = institutional_control_center(symbol)
    lines = [
        "🏛️ V300 INSTITUTIONAL CONTROL CENTER",
        f"เวลาไทย: {p.get('time_th')}",
        f"System Score: {p.get('system_score')} | Decision: {p.get('decision')}",
        "",
        "COMPONENT SCORES",
    ]
    for k,v in p.get("component_scores", {}).items():
        lines.append(f"- {k}: {v}")
    lines += [
        "",
        "DATA BUS",
        f"Decision: {p.get('data_bus',{}).get('decision')} | Bad sources: {len(p.get('data_bus',{}).get('bad_sources', []))}",
        "",
        "MODEL REGISTRY",
        f"Models: {len(p.get('model_registry',{}).get('models', []))} | Drift alerts: {len(p.get('model_registry',{}).get('drift_alerts', []))}",
        "",
        "EXPLAINABILITY",
        p.get("explainability",{}).get("explanation"),
        "",
        "Safety: Paper-first / Decision Support. ไม่รับประกันกำไร และควรใช้เงินจริงเฉพาะหลัง forward test",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
