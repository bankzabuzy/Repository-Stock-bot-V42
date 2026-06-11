
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any, Dict
from .common import init_db, connect, V120_VERSION, safety_event
from .risk_pretrade import pretrade_check, classify_asset
from .broker_adapters import get_adapter

def create_order_intent(symbol: str, side: str="BUY", qty: Any=1, order_type: str="MARKET", broker: str="PAPER", mode: str="PAPER", limit_price: Any=None, stop_price: Any=None, market_price: Any=None) -> Dict[str, Any]:
    init_db()
    intent = {
        "symbol": symbol.upper(),
        "side": side.upper(),
        "qty": float(qty),
        "order_type": order_type.upper(),
        "broker": broker.upper(),
        "mode": mode.upper(),
        "limit_price": float(limit_price) if limit_price not in {None, ""} else None,
        "stop_price": float(stop_price) if stop_price not in {None, ""} else None,
        "market_price": float(market_price) if market_price not in {None, ""} else None,
        "asset_class": classify_asset(symbol),
    }
    check = pretrade_check(intent)
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO v120_order_intents(created_at,symbol,side,qty,order_type,limit_price,stop_price,broker,mode,approval_status,reason,payload,model_version)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            datetime.now(timezone.utc).isoformat(), intent["symbol"], intent["side"], intent["qty"], intent["order_type"],
            intent["limit_price"], intent["stop_price"], intent["broker"], intent["mode"], check["decision"],
            ",".join(check.get("failed", [])), json.dumps(intent, ensure_ascii=False), V120_VERSION
        ))
        conn.commit()
        intent_id = cur.lastrowid
        conn.close()
    except Exception as e:
        return {"ok": False, "error": str(e), "intent": intent, "pretrade": check}
    return {"ok": True, "intent_id": intent_id, "intent": intent, "pretrade": check}

def route_order(intent_id: int) -> Dict[str, Any]:
    init_db()
    try:
        conn = connect()
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM v120_order_intents WHERE id=?", (intent_id,))
        row = cur.fetchone()
        if not row:
            return {"ok": False, "reason": "intent_not_found"}
        rec = dict(row)
        intent = json.loads(rec.get("payload") or "{}")
        if rec.get("approval_status") != "APPROVED":
            return {"ok": False, "status": "BLOCKED", "reason": rec.get("reason"), "pretrade": rec.get("approval_status")}
        adapter = get_adapter(rec.get("broker"))
        result = adapter.place_order(intent)
        cur.execute("""
            INSERT INTO v120_order_results(intent_id,created_at,broker,status,order_id,filled_price,filled_qty,error,model_version)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (intent_id, datetime.now(timezone.utc).isoformat(), result.get("broker"), result.get("status"), result.get("order_id"), result.get("filled_price"), result.get("filled_qty"), result.get("error") or result.get("reason"), V120_VERSION))
        conn.commit()
        conn.close()
        safety_event("order_router", f"Order routed {rec.get('symbol')} {rec.get('side')}", payload=result)
        return {"ok": bool(result.get("ok")), "intent_id": intent_id, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_and_route(symbol: str, side: str="BUY", qty: Any=1, broker: str="PAPER", mode: str="PAPER", price: Any=None) -> Dict[str, Any]:
    created = create_order_intent(symbol, side, qty, "MARKET", broker, mode, market_price=price)
    if not created.get("ok"):
        return created
    if created.get("pretrade",{}).get("decision") != "APPROVED":
        return {**created, "routed": False}
    routed = route_order(created["intent_id"])
    return {**created, "routed": routed}
