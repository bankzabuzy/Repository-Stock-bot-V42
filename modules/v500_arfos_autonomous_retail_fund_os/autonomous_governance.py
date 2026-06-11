
from __future__ import annotations
import os, json
from datetime import datetime, timezone
from .common import init_db, connect, V500_VERSION

DEFAULT_POLICIES = {
    "MAX_DAILY_DD": ("5", "CRITICAL"),
    "MAX_TOTAL_DD": ("15", "CRITICAL"),
    "LIVE_TRADING_ALLOWED": ("false", "CRITICAL"),
    "REQUIRE_FORWARD_TEST_DAYS": ("90", "HIGH"),
    "REQUIRE_BROKER_VERIFICATION": ("true", "HIGH"),
    "LINE_ALERT_A_PLUS_ONLY": ("true", "MEDIUM"),
    "HUMAN_OVERRIDE_REQUIRES_TOKEN": ("true", "CRITICAL"),
}

def seed_governance_policy():
    init_db()
    conn = connect(); cur = conn.cursor()
    for k, (v, sev) in DEFAULT_POLICIES.items():
        cur.execute("INSERT OR IGNORE INTO v500_governance_policy(policy_key,policy_value,severity,enabled,updated_at,model_version) VALUES(?,?,?,?,?,?)",
                    (k, v, sev, 1, datetime.now(timezone.utc).isoformat(), V500_VERSION))
    conn.commit(); conn.close()
    return {"ok": True}

def governance_status():
    seed_governance_policy()
    conn = connect(); conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM v500_governance_policy")
    policies = [dict(r) for r in cur.fetchall()]
    conn.close()

    live_allowed_env = os.getenv("ALLOW_LIVE_TRADING", "false").lower() in {"1","true","yes"}
    live_policy = next((p for p in policies if p["policy_key"] == "LIVE_TRADING_ALLOWED"), {})
    live_policy_allowed = str(live_policy.get("policy_value","false")).lower() in {"1","true","yes"}
    broker_verified = False
    try:
        from modules.v220_broker_execution_network.broker_network import broker_status
        bs = broker_status()
        broker_verified = any(b.get("configured") and not b.get("safe_mode") for b in bs.get("items", []) if b.get("broker") != "PAPER")
    except Exception:
        broker_verified = False

    decision = "PAPER_ONLY"
    if live_allowed_env and live_policy_allowed and broker_verified:
        decision = "LIVE_READY_REQUIRES_FINAL_HUMAN_APPROVAL"
    return {"ok": True, "version": V500_VERSION, "decision": decision, "live_allowed_env": live_allowed_env, "broker_verified": broker_verified, "policies": policies}
