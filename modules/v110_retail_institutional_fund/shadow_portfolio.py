
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any
from .common import init_db, connect

DEFAULT_PORTFOLIOS = {
    "Conservative": {"SPY": 30, "QQQ": 15, "THAI_GOLD": 20, "CASH": 35},
    "Balanced": {"SPY": 25, "QQQ": 25, "NVDA": 8, "TSM": 7, "THAI_GOLD": 15, "CASH": 20},
    "Aggressive": {"QQQ": 30, "NVDA": 15, "TSM": 10, "AMD": 8, "THAI_GOLD": 12, "CASH": 25},
}

def ensure_shadow_portfolios() -> Dict[str, Any]:
    init_db()
    conn = connect()
    cur = conn.cursor()
    for name, holdings in DEFAULT_PORTFOLIOS.items():
        for sym, w in holdings.items():
            cur.execute("""
                INSERT OR IGNORE INTO v110_shadow_portfolio(portfolio_name,symbol,weight,last_pnl,updated_at)
                VALUES(?,?,?,?,?)
            """, (name, sym, w, 0.0, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()
    return {"ok": True, "portfolios": list(DEFAULT_PORTFOLIOS)}

def shadow_summary() -> Dict[str, Any]:
    ensure_shadow_portfolios()
    try:
        conn = connect()
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM v110_shadow_portfolio ORDER BY portfolio_name, symbol")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        groups = {}
        for r in rows:
            groups.setdefault(r["portfolio_name"], []).append(r)
        summary = []
        for name, items in groups.items():
            summary.append({"portfolio": name, "holdings": items, "weight_sum": round(sum(i["weight"] for i in items), 2)})
        return {"ok": True, "items": summary}
    except Exception as e:
        return {"ok": False, "error": str(e), "items": []}
