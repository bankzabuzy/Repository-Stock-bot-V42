
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from .common import init_db, connect, safe_float, env_bool, V220_VERSION
from .broker_network import choose_broker, classify_symbol

def pretrade_check(symbol: str, side: str, qty, price=None, mode: str="PAPER") -> dict:
    qty_f = safe_float(qty, 0) or 0
    price_f = safe_float(price, 100) or 100
    notional = abs(qty_f * price_f)
    max_notional = safe_float(__import__("os").getenv("V220_MAX_ORDER_NOTIONAL", "10000"), 10000) or 10000
    checks = {
        "symbol_supported": classify_symbol(symbol) != "UNKNOWN",
        "qty_positive": qty_f > 0,
        "notional_ok": notional <= max_notional,
        "live_allowed": mode.upper() != "LIVE" or env_bool("ALLOW_LIVE_TRADING"),
    }
    failed = [k for k,v in checks.items() if not v]
    return {"ok": not failed, "checks": checks, "failed": failed, "notional": round(notional,2), "decision": "APPROVED" if not failed else "BLOCKED"}

def route_execution(symbol: str="SPY", side: str="BUY", qty=1, price=None, preferred_broker: str="PAPER", mode: str="PAPER") -> dict:
    init_db()
    broker = choose_broker(symbol, preferred_broker)
    check = pretrade_check(symbol, side, qty, price, mode)
    if not check["ok"]:
        result = {"ok": False, "status": "BLOCKED_PRETRADE", "pretrade": check, "broker": broker}
    else:
        if broker["broker"] == "PAPER":
            result = {"ok": True, "status": "ACCEPTED_SIM", "order_id": "PAPER-" + uuid.uuid4().hex[:12].upper(), "broker": "PAPER"}
        else:
            result = {"ok": False, "status": "BLOCKED_SAFE_STUB", "broker": broker["broker"], "reason": "Live broker adapter is safe-stub until final credential validation"}
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v220_execution_requests(created_at,symbol,side,qty,broker,mode,pretrade_status,routing_status,result,model_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), symbol.upper(), side.upper(), safe_float(qty,0), broker["broker"], mode.upper(), check["decision"], result["status"], json.dumps(result, ensure_ascii=False, default=str), V220_VERSION))
        conn.commit(); conn.close()
    except Exception:
        pass
    return {"ok": result.get("ok", False), "broker_selection": broker, "pretrade": check, "result": result}
