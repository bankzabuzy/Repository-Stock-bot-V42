
from __future__ import annotations
from .common import V220_VERSION, now_th, init_db
from .broker_network import broker_status
from .pretrade_router import route_execution
from .compatibility import compatibility_report

def build_v220_payload(symbol: str="SPY"):
    init_db()
    return {
        "ok": True,
        "version": V220_VERSION,
        "time_th": now_th(),
        "broker_network": broker_status(),
        "paper_route_test": route_execution(symbol, "BUY", 1, 100, "PAPER", "PAPER"),
        "compatibility": compatibility_report(True),
        "endpoints": ["/v220/broker-network", "/v220/broker-network-json", "/v220/route-test", "/v220/compatibility"],
    }

def build_v220_text(symbol: str="SPY") -> str:
    p = build_v220_payload(symbol)
    brokers = p["broker_network"]["items"]
    route = p["paper_route_test"]
    comp = p["compatibility"]
    lines = [
        "🔗 V220 BROKER EXECUTION NETWORK & COMPATIBILITY",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        "BROKER NETWORK",
    ]
    for b in brokers:
        lines.append(f"- {b.get('broker')}: {b.get('status')} | configured={b.get('configured')} | safe_mode={b.get('safe_mode')}")
    lines += [
        "",
        "PAPER ROUTE TEST",
        f"Broker: {route.get('broker_selection',{}).get('broker')} | Pretrade: {route.get('pretrade',{}).get('decision')} | Result: {route.get('result',{}).get('status')}",
        "",
        "COMPATIBILITY",
        f"Imports: {'✅' if comp.get('imports',{}).get('ok') else '❌'} | Routes: {comp.get('routes',{}).get('route_count')} | Collisions: {comp.get('routes',{}).get('collision_count')}",
        "",
        "Safety: non-PAPER brokers are safe-stub unless credentials and ALLOW_LIVE_TRADING are validated.",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
