
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Dict, Any
from .common import init_db, connect, V130_VERSION, env_bool, log_incident
from .capital_allocation import allocation_plan

def autonomous_mode_status() -> Dict[str, Any]:
    enabled = env_bool("V130_AUTONOMOUS_MODE", "false")
    paper_only = not env_bool("ALLOW_LIVE_TRADING", "false")
    return {
        "ok": True,
        "enabled": enabled,
        "paper_only": paper_only,
        "mode": "AUTONOMOUS_PAPER" if enabled and paper_only else "AUTONOMOUS_LIVE" if enabled else "MANUAL_APPROVAL",
        "safety": "LIVE orders blocked unless ALLOW_LIVE_TRADING=true",
    }

def generate_rebalance_intents() -> Dict[str, Any]:
    init_db()
    status = autonomous_mode_status()
    plan = allocation_plan()
    created = []
    if not status.get("enabled"):
        return {"ok": True, "created": [], "reason": "autonomous_mode_disabled", "plan": plan}
    try:
        conn = connect()
        cur = conn.cursor()
        for item in plan.get("items", []):
            if item.get("action") in {"ADD", "REDUCE"}:
                side = "BUY" if item["action"] == "ADD" else "SELL"
                symbol = item["bucket"]
                cur.execute("INSERT INTO v130_rebalance_orders(created_at,symbol,side,target_weight,current_weight,order_status,reason,model_version) VALUES(?,?,?,?,?,?,?,?)",
                            (datetime.now(timezone.utc).isoformat(), symbol, side, item["target_weight"], item["current_weight"], "PENDING_APPROVAL", f"drift {item['drift']}%", V130_VERSION))
                created.append({"id": cur.lastrowid, "symbol": symbol, "side": side, "reason": f"drift {item['drift']}%"})
        conn.commit()
        conn.close()
        return {"ok": True, "mode": status.get("mode"), "created": created, "plan": plan}
    except Exception as e:
        log_incident("autonomous_controls", "generate_rebalance_intents_failed", "ERROR", str(e))
        return {"ok": False, "error": str(e)}
