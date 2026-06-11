
from __future__ import annotations
from typing import Dict, Any
from .common import V120_VERSION, now_th, init_db
from .broker_adapters import all_broker_status
from .portfolio_sync import portfolio_snapshot
from .common import connect

def recent_orders(limit: int=10) -> Dict[str, Any]:
    init_db()
    try:
        conn = connect()
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM v120_order_intents ORDER BY id DESC LIMIT ?", (limit,))
        intents = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT * FROM v120_order_results ORDER BY id DESC LIMIT ?", (limit,))
        results = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"ok": True, "intents": intents, "results": results}
    except Exception as e:
        return {"ok": False, "error": str(e), "intents": [], "results": []}

def build_v120_payload() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": V120_VERSION,
        "time_th": now_th(),
        "db": init_db(),
        "brokers": all_broker_status(),
        "portfolio": portfolio_snapshot(),
        "orders": recent_orders(),
        "endpoints": ["/v120/broker-center", "/v120/broker-center-json", "/v120/brokers", "/v120/order-test", "/v120/portfolio"],
    }

def build_v120_text() -> str:
    p = build_v120_payload()
    brokers = p.get("brokers",{}).get("items", [])
    port = p.get("portfolio", {})
    orders = p.get("orders", {})
    lines = [
        "🔌 V120 BROKER LIVE-READY SAFETY LAYER",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        "BROKERS",
    ]
    for b in brokers:
        lines.append(f"- {b.get('broker')}: {'✅' if b.get('ok') else '⚠️'} | configured={b.get('configured', b.get('connected'))} | {b.get('message')}")
    lines += [
        "",
        "PORTFOLIO SNAPSHOT",
        f"Positions: {port.get('count')} | Total MV: {port.get('total_market_value')}",
        "",
        "RECENT ORDERS",
        f"Intents: {len(orders.get('intents', []))} | Results: {len(orders.get('results', []))}",
        "",
        "Safety: LIVE blocked unless ALLOW_LIVE_TRADING=true",
        "Quick: /v120/order-test?symbol=SPY&side=BUY&qty=1&broker=PAPER&price=500",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
