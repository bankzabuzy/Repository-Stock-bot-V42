
from __future__ import annotations
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
from .security import safe_public_config
from .state import init_state_db, last_errors, get_state
from .guardrails import alert_gate, maintenance_mode, live_trading_guard
from .selftest import full_self_test
from .backup import db_summary

V101_VERSION = "V1419_MASTER_CLEAN_FINAL"

def _now_th() -> str:
    return datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")

def build_v101_payload() -> Dict[str, Any]:
    db = init_state_db()
    cfg = safe_public_config()
    gate = alert_gate()
    errors = last_errors(10)
    dbs = db_summary()
    return {
        "ok": bool(db.get("ok")),
        "version": V101_VERSION,
        "time_th": _now_th(),
        "database": db,
        "config": cfg,
        "alert_gate": gate,
        "maintenance": maintenance_mode(),
        "live_trading_guard": live_trading_guard(),
        "db_summary": dbs,
        "last_errors": errors,
        "commands": {
            "line": ["status", "v100", "v101", "pause alerts", "resume alerts", "last error"],
            "endpoints": ["/v101/production-center", "/v101/self-test", "/v101/config", "/v101/errors", "/v101/db-summary"],
        },
    }

def build_v101_text() -> str:
    p = build_v101_payload()
    cfg = p.get("config", {})
    gate = p.get("alert_gate", {})
    dbs = p.get("db_summary", {})
    errors = p.get("last_errors", {}).get("items", [])
    lines = [
        "🛡️ V101 PRODUCTION HARDENING & SECURITY",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        f"System: {'✅ OK' if p.get('ok') else '❌ CHECK'}",
        f"Alert Gate: {gate.get('decision')} | Checks: {gate.get('checks')}",
        f"Maintenance: {p.get('maintenance',{}).get('decision')}",
        f"Live Guard: {p.get('live_trading_guard',{}).get('decision')}",
        "",
        "CONFIG",
        f"Fund Mode: {cfg.get('fund_mode')} | Live Enabled: {cfg.get('live_trading_enabled')}",
        f"ADMIN_TOKEN: {'✅' if cfg.get('env_present',{}).get('ADMIN_TOKEN') else '❌'} | LINE: {'✅' if cfg.get('line_config_set') else '❌'}",
        "",
        "DATABASE",
        f"DB: {dbs.get('db')} | Tables: {len(dbs.get('tables',{}))}",
        "",
        "LAST ERRORS",
    ]
    if errors:
        for e in errors[:5]:
            lines.append(f"- {e.get('component')} | {e.get('severity')} | {e.get('message')}")
    else:
        lines.append("- ไม่มี error ล่าสุด")
    lines += [
        "",
        "Endpoints: /v101/production-center | /v101/self-test | /v101/config | /v101/errors",
        f"Version : {V101_VERSION}",
    ]
    return "\n".join(lines)
