
from __future__ import annotations
import os
from typing import Dict, Any
from .state import get_state

V101_VERSION = "V1419_MASTER_CLEAN_FINAL"

def maintenance_mode() -> Dict[str, Any]:
    enabled = get_state("maintenance_mode", os.getenv("MAINTENANCE_MODE", "false")).lower() in {"1","true","yes","on"}
    return {
        "enabled": enabled,
        "decision": "SYSTEM_PAUSED" if enabled else "ACTIVE",
        "rule": "เมื่อ maintenance_mode=true ระบบควรงดส่ง alert/ไม่เปิด order ใหม่",
    }

def live_trading_guard() -> Dict[str, Any]:
    allow = os.getenv("ALLOW_LIVE_TRADING", "false").lower() in {"1","true","yes"}
    mode = os.getenv("FUND_MODE", "PAPER").upper()
    safe = (mode != "LIVE") or allow
    return {
        "ok": safe,
        "fund_mode": mode,
        "allow_live_trading": allow,
        "decision": "ALLOW" if safe else "BLOCK_LIVE_TRADING",
        "rule": "LIVE ต้องตั้ง ALLOW_LIVE_TRADING=true เท่านั้น",
    }

def alert_gate() -> Dict[str, Any]:
    maint = maintenance_mode()
    live = live_trading_guard()
    checks = {
        "maintenance_off": not maint.get("enabled"),
        "live_guard_ok": bool(live.get("ok")),
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "maintenance": maint,
        "live_guard": live,
        "decision": "ALLOW_ALERTS" if all(checks.values()) else "BLOCK_ALERTS",
    }
