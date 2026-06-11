
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, V500_VERSION
from .arfos_core import arfos_status, arfos_text, compatibility_audit

def phase4_center(symbol="SPY"):
    init_db()
    arfos = arfos_status(symbol)
    comp = compatibility_audit()
    score = arfos.get("readiness_score", 0)
    payload = {"ok": True, "version": V500_VERSION, "phase4_score": score, "arfos": arfos, "compatibility": comp}
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v500_phase4_audit(created_at,latest_version,compile_ok,route_collision_count,compatibility_ok,phase4_score,report) VALUES(?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), V500_VERSION, 1, comp.get("route_collision_count", 0), 1 if comp.get("ok") else 0, score, json.dumps(payload, ensure_ascii=False, default=str)))
        conn.commit(); conn.close()
    except Exception:
        pass
    return payload

def phase4_text(symbol="SPY"):
    return arfos_text(symbol)
