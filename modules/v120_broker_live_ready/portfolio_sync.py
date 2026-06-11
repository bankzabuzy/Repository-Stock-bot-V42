
from __future__ import annotations
from typing import Dict, Any
from .common import init_db, connect

def portfolio_snapshot() -> Dict[str, Any]:
    init_db()
    items = []
    try:
        conn = connect()
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.cursor()
        # Merge existing V110 positions style if fund_positions exists.
        for table in ["fund_positions", "v51_portfolio_positions"]:
            try:
                cur.execute(f"SELECT * FROM {table}")
                items += [dict(r) | {"source_table": table} for r in cur.fetchall()]
            except Exception:
                pass
        conn.close()
    except Exception as e:
        return {"ok": False, "error": str(e), "items": []}
    total = 0
    for i in items:
        try:
            total += float(i.get("market_value") or 0)
        except Exception:
            pass
    return {"ok": True, "items": items, "total_market_value": round(total, 2), "count": len(items)}
