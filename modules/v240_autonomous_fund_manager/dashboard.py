
from __future__ import annotations
from .common import V240_VERSION, now_th, init_db
from .investment_committee import investment_committee
from .capital_flow_regime import regime_switching, global_capital_flow
from .fund_health_auto_pause import fund_health_score, auto_pause_engine
from .watchlist_journal import watchlist_rank, journal_event
from .compatibility import compatibility_report

def build_v240_payload(symbol: str="SPY"):
    init_db()
    committee = investment_committee(symbol)
    regime = regime_switching()
    health = fund_health_score()
    pause = auto_pause_engine()
    watch = watchlist_rank()
    comp = compatibility_report(True)
    journal_event("SYSTEM_CHECK", symbol, committee.get("final_decision"), "V240 dashboard generated", str(regime), regime.get("regime"), {"health": health})
    return {"ok": True, "version": V240_VERSION, "time_th": now_th(), "symbol": symbol, "committee": committee, "capital_flow": global_capital_flow(), "regime_switching": regime, "fund_health": health, "auto_pause": pause, "watchlist": watch, "compatibility": comp}

def build_v240_text(symbol: str="SPY"):
    p = build_v240_payload(symbol)
    h = p["fund_health"]
    c = p["committee"]
    r = p["regime_switching"]
    w = p["watchlist"]["items"][:5]
    comp = p["compatibility"]
    lines = [
        "🏦 V240 AUTONOMOUS FUND MANAGER",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        "INVESTMENT COMMITTEE",
        f"Symbol: {symbol} | Decision: {c.get('final_decision')} | Score: {c.get('final_score')} | Votes: {c.get('votes')}",
        "",
        "FUND HEALTH",
        f"Score: {h.get('health_score')} | Decision: {h.get('decision')} | Components: {h.get('components')}",
        "",
        "REGIME / CAPITAL FLOW",
        f"Regime: {r.get('regime')} | Allocation Bias: {r.get('allocation_bias')}",
        "",
        "WATCHLIST TOP",
    ]
    for i, item in enumerate(w, 1):
        lines.append(f"{i}. {item.get('symbol')} | Score {item.get('score')} | {item.get('committee_decision')} | Change {item.get('change_pct')}%")
    lines += [
        "",
        f"Auto Pause: {'ACTIVE' if p.get('auto_pause',{}).get('active') else 'OK'} | Triggers: {p.get('auto_pause',{}).get('triggers')}",
        f"Compatibility: imports={'OK' if comp.get('imports',{}).get('ok') else 'CHECK'} | routes={comp.get('routes',{}).get('route_count')} | collisions={comp.get('routes',{}).get('collision_count')}",
        "",
        "Safety: Decision Support / Paper-first. ไม่รับประกันกำไร และยังไม่ควรยิงเงินจริงถ้าไม่ผ่าน forward test",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
