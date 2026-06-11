
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from .common import init_db, connect, V470_VERSION

def investor_dashboard():
    init_db()
    # Pull real forward-test proof if available; otherwise use warmup mode
    conn = connect(); conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    try:
        cur.execute("SELECT result_r FROM v350_forward_tests WHERE result_r IS NOT NULL")
        rs = [float(r["result_r"]) for r in cur.fetchall()]
    except Exception:
        rs = []
    warmup = not bool(rs)
    if warmup:
        rs = [0.4, -0.25, 0.7, -0.1, 0.9, 0.2, -0.35]
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r < 0]
    mean = sum(rs)/len(rs)
    std = math.sqrt(sum((r-mean)**2 for r in rs)/max(1, len(rs)-1))
    sharpe = mean/std*math.sqrt(252) if std else None
    downside = [min(0,r) for r in rs]
    downstd = math.sqrt(sum(r*r for r in downside)/max(1, len(downside)))
    sortino = mean/downstd*math.sqrt(252) if downstd else None
    pf = sum(wins)/abs(sum(losses)) if losses else None
    nav = 100000 + sum(rs)*1000
    equity = peak = maxdd = 0
    for r in rs:
        equity += r
        peak = max(peak, equity)
        maxdd = max(maxdd, peak-equity)
    rolling = mean * 30
    cagr = mean * 252
    exposure = {"Equity": 55, "Gold": 15, "Cash": 20, "Crypto": 5, "Tactical": 5}
    report = {
        "warmup_mode": warmup,
        "nav": round(nav,2),
        "cagr": round(cagr,2),
        "rolling_return": round(rolling,2),
        "drawdown": round(maxdd,3),
        "profit_factor": round(pf,2) if pf else None,
        "sharpe": round(sharpe,2) if sharpe else None,
        "sortino": round(sortino,2) if sortino else None,
        "exposure": exposure,
        "sample_size": len(rs),
    }
    cur.execute("INSERT INTO v470_investor_dashboard(created_at,nav,cagr,rolling_return,drawdown,profit_factor,sharpe,sortino,exposure,report,model_version) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), report["nav"], report["cagr"], report["rolling_return"], report["drawdown"], report["profit_factor"], report["sharpe"], report["sortino"], json.dumps(exposure, ensure_ascii=False), json.dumps(report, ensure_ascii=False), V470_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V470_VERSION, **report}
