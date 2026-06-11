
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, price, safe_float, V500_VERSION

def _ai_decision(symbol):
    try:
        from modules.v470_phase3_meta_selfheal_dashboard.dashboard import phase3_center
        p = phase3_center(symbol)
        return (p.get("explainable_report") or {}).get("decision", "WAIT"), p
    except Exception as e:
        return "WAIT", {"ok": False, "error": str(e)}

def shadow_real_money(symbol="SPY", human_decision="WAIT"):
    init_db()
    ai_decision, ai_payload = _ai_decision(symbol)
    snap = price(symbol)
    chg = safe_float(snap.get("change_pct"), 0) or 0

    def pnl_for(decision):
        if decision in {"BUY","APPROVED_BUY"}:
            return chg / 10
        if decision in {"SELL","SHORT"}:
            return -chg / 10
        return 0

    ai_pnl = pnl_for(ai_decision)
    human_pnl = pnl_for(human_decision)
    bench_pnl = chg / 10
    divergence = abs(ai_pnl - human_pnl) + abs(ai_pnl - bench_pnl)

    report = {
        "symbol": symbol,
        "snapshot": snap,
        "ai_decision": ai_decision,
        "human_decision": human_decision,
        "benchmark_decision": "BUY_SPY_BENCHMARK",
        "ai_pnl_r": round(ai_pnl, 4),
        "human_pnl_r": round(human_pnl, 4),
        "benchmark_pnl_r": round(bench_pnl, 4),
        "divergence_score": round(divergence, 4),
        "ai_payload": ai_payload,
        "mode": "SHADOW_ONLY_NO_LIVE_ORDER",
    }
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v500_shadow_real_money(created_at,symbol,ai_decision,human_decision,benchmark_decision,ai_pnl_r,human_pnl_r,benchmark_pnl_r,divergence_score,report,model_version) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), symbol.upper(), ai_decision, human_decision, "BUY_SPY_BENCHMARK", ai_pnl, human_pnl, bench_pnl, divergence, json.dumps(report, ensure_ascii=False, default=str), V500_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V500_VERSION, **report}
