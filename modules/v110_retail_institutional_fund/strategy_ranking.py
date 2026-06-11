
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any
from .common import init_db, connect

def seed_strategy_scores() -> None:
    init_db()
    defaults = [
        ("Trend Following", 54.0, 1.35, 1.1, 8.0),
        ("Mean Reversion", 49.0, 1.05, 0.5, 12.0),
        ("Momentum", 57.0, 1.55, 1.4, 7.5),
        ("Breakout", 51.0, 1.18, 0.8, 10.0),
    ]
    conn = connect()
    cur = conn.cursor()
    for row in defaults:
        cur.execute("""
            INSERT OR IGNORE INTO v110_strategy_scoreboard(strategy,win_rate,profit_factor,sharpe,max_dd,enabled,updated_at)
            VALUES(?,?,?,?,?,?,?)
        """, (*row, 1, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()

def strategy_ranking() -> Dict[str, Any]:
    seed_strategy_scores()
    try:
        conn = connect()
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM v110_strategy_scoreboard")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        for r in rows:
            score = (r.get("win_rate") or 0)*0.35 + (r.get("profit_factor") or 0)*20 + (r.get("sharpe") or 0)*12 - (r.get("max_dd") or 0)*0.8
            r["strategy_score"] = round(score, 2)
            r["recommended_state"] = "ACTIVE" if score >= 45 else "WATCH" if score >= 35 else "PAUSE"
        rows.sort(key=lambda x: x.get("strategy_score", 0), reverse=True)
        return {"ok": True, "items": rows}
    except Exception as e:
        return {"ok": False, "error": str(e), "items": []}
