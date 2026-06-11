
from __future__ import annotations
import os, json
from datetime import datetime, timezone
from typing import Any, Dict, List
from .common import init_db, connect, V130_VERSION, env_bool, now_th, log_incident

def _check_env() -> Dict[str, Any]:
    keys = ["ADMIN_TOKEN", "DB_PATH", "LINE_CHANNEL_ACCESS_TOKEN", "ALLOW_LIVE_TRADING", "BROKER_DEFAULT"]
    present = {k: bool(os.getenv(k)) for k in keys}
    score = sum(1 for v in present.values() if v) / len(keys) * 100
    return {"name": "environment", "ok": score >= 60, "score": round(score,2), "detail": present}

def _check_v120() -> Dict[str, Any]:
    try:
        from modules.v120_broker_live_ready.broker_adapters import all_broker_status
        data = all_broker_status()
        paper_ok = any(x.get("broker") == "PAPER" and x.get("ok") for x in data.get("items", []))
        return {"name": "v120_broker_layer", "ok": paper_ok, "score": 100 if paper_ok else 40, "detail": data}
    except Exception as e:
        return {"name": "v120_broker_layer", "ok": False, "score": 0, "detail": str(e)}

def _check_v110() -> Dict[str, Any]:
    try:
        from modules.v110_retail_institutional_fund.master_dashboard import build_master_payload
        data = build_master_payload()
        return {"name": "v110_fund_platform", "ok": bool(data.get("ok")), "score": 100 if data.get("ok") else 30, "detail": {"version": data.get("version")}}
    except Exception as e:
        return {"name": "v110_fund_platform", "ok": False, "score": 0, "detail": str(e)}

def _check_live_guard() -> Dict[str, Any]:
    live = env_bool("ALLOW_LIVE_TRADING")
    mode = os.getenv("FUND_MODE", "PAPER").upper()
    ok = (mode != "LIVE") or live
    return {"name": "live_guard", "ok": ok, "score": 100 if ok else 0, "detail": {"FUND_MODE": mode, "ALLOW_LIVE_TRADING": live}}

def run_readiness_checks() -> Dict[str, Any]:
    init_db()
    checks = [_check_env(), _check_v120(), _check_v110(), _check_live_guard()]
    overall = round(sum(c.get("score",0) for c in checks) / max(1, len(checks)), 2)
    status = "LIVE_READY_PAPER_ONLY" if overall >= 80 and all(c.get("ok") for c in checks) else "NOT_READY"
    if os.getenv("FUND_MODE", "PAPER").upper() == "LIVE" and not env_bool("ALLOW_LIVE_TRADING"):
        status = "LIVE_BLOCKED_BY_SAFETY"
    try:
        conn = connect()
        cur = conn.cursor()
        for c in checks:
            cur.execute("INSERT INTO v130_readiness_checks(created_at,check_name,status,score,detail,model_version) VALUES(?,?,?,?,?,?)",
                        (datetime.now(timezone.utc).isoformat(), c["name"], "PASS" if c.get("ok") else "FAIL", c.get("score"), json.dumps(c.get("detail"), ensure_ascii=False, default=str), V130_VERSION))
        conn.commit()
        conn.close()
    except Exception as e:
        log_incident("readiness", "failed_to_record_checks", "ERROR", str(e))
    return {"ok": status != "NOT_READY", "version": V130_VERSION, "time_th": now_th(), "overall_score": overall, "status": status, "checks": checks}
