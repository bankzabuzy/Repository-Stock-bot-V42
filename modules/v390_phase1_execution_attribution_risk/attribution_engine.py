
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, V390_VERSION

def attribution_report():
    init_db()
    # Uses forward-test result_r when available; otherwise produces warmup attribution buckets.
    conn = connect(); conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    try:
        cur.execute("SELECT symbol,result_r FROM v350_forward_tests WHERE result_r IS NOT NULL")
        rows = [dict(r) for r in cur.fetchall()]
    except Exception:
        rows = []
    if not rows:
        rows = [
            {"symbol": "SPY", "result_r": 0.4},
            {"symbol": "QQQ", "result_r": 0.7},
            {"symbol": "GC=F", "result_r": -0.2},
        ]
        warmup = True
    else:
        warmup = False
    buckets = {}
    for r in rows:
        sym = r["symbol"]
        if sym in {"SPY","QQQ"}:
            strat = "Index Momentum"
        elif sym in {"GC=F","XAUUSD","GOLD"}:
            strat = "Macro Gold Hedge"
        else:
            strat = "Single Stock Tactical"
        buckets[strat] = buckets.get(strat, 0) + float(r.get("result_r") or 0)
    total_abs = sum(abs(v) for v in buckets.values()) or 1
    items = []
    for strat, val in buckets.items():
        pct = val / total_abs * 100
        item = {"strategy": strat, "contribution_r": round(val, 3), "contribution_pct": round(pct, 2)}
        items.append(item)
        cur.execute("INSERT INTO v390_attribution(created_at,symbol,strategy,macro_regime,contribution_r,contribution_pct,report,model_version) VALUES(?,?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), "PORTFOLIO", strat, "MIXED", val, pct, json.dumps(item, ensure_ascii=False), V390_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V390_VERSION, "warmup_mode": warmup, "items": items, "total_r": round(sum(buckets.values()), 3)}
