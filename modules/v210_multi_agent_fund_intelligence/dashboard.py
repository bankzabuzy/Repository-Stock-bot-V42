
from __future__ import annotations
from .common import V210_VERSION, now_th, init_db
from .committee import committee_decision
from .compatibility import compatibility_report

def build_v210_payload(symbol: str="SPY") -> dict:
    init_db()
    return {
        "ok": True,
        "version": V210_VERSION,
        "time_th": now_th(),
        "symbol": symbol,
        "committee": committee_decision(symbol),
        "compatibility": compatibility_report(True),
        "endpoints": ["/v210/agent-center", "/v210/agent-center-json", "/v210/agents", "/v210/compatibility"],
    }

def build_v210_text(symbol: str="SPY") -> str:
    p = build_v210_payload(symbol)
    c = p["committee"]
    comp = p["compatibility"]
    lines = [
        "🤖 V210 MULTI-AGENT FUND INTELLIGENCE",
        f"เวลาไทย: {p.get('time_th')}",
        f"Symbol: {symbol}",
        "",
        "COMMITTEE DECISION",
        f"Final: {c.get('final_decision')} | Confidence: {c.get('final_confidence')}% | Override: {c.get('risk_override')}",
        f"Votes: {c.get('counts')} | Agreement: {c.get('agreement_pct')}%",
        "",
        "AGENTS",
    ]
    for v in c.get("votes", []):
        lines.append(f"- {v.get('agent')}: {v.get('vote')} | Conf {v.get('confidence')} | {v.get('reasoning')}")
    lines += [
        "",
        "COMPATIBILITY",
        f"Imports: {'✅' if comp.get('imports',{}).get('ok') else '❌'} | Routes: {comp.get('routes',{}).get('route_count')} | Collisions: {comp.get('routes',{}).get('collision_count')}",
        "",
        "หมายเหตุ: V210 เป็น Multi-Agent Committee Layer ต่อจาก V200 ไม่ลบ endpoint เดิม",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
