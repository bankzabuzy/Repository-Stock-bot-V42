
from __future__ import annotations
import random, os
from datetime import datetime, timezone
from typing import Any, Dict
from .common import init_db, connect, safe_float, V110_VERSION

def simulate_execution(symbol: str, side: str="BUY", expected_price: Any=None, qty: Any=1) -> Dict[str, Any]:
    init_db()
    expected = safe_float(expected_price, 100.0) or 100.0
    qty_f = safe_float(qty, 1.0) or 1.0
    spread_bps = safe_float(os.getenv("V110_SPREAD_BPS", "8"), 8) or 8
    slippage_bps = safe_float(os.getenv("V110_SLIPPAGE_BPS", "12"), 12) or 12
    commission_min = safe_float(os.getenv("V110_COMMISSION_MIN", "0.35"), 0.35) or 0.35

    direction = 1 if side.upper() == "BUY" else -1
    spread = expected * spread_bps / 10000
    slippage = expected * slippage_bps / 10000 * random.uniform(0.4, 1.4)
    filled = expected + direction * (spread/2 + slippage)
    commission = max(commission_min, abs(qty_f * filled) * 0.0003)
    delay_ms = int(random.uniform(120, 1800))
    status = "FILLED_SIM"

    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO v110_execution_sim(created_at,symbol,expected_price,filled_price,side,qty,spread,slippage,commission,delay_ms,status,model_version)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """, (datetime.now(timezone.utc).isoformat(), symbol.upper(), expected, filled, side.upper(), qty_f, spread, slippage, commission, delay_ms, status, V110_VERSION))
        conn.commit()
        rid = cur.lastrowid
        conn.close()
    except Exception:
        rid = None

    return {
        "ok": True,
        "id": rid,
        "symbol": symbol.upper(),
        "side": side.upper(),
        "expected_price": round(expected, 4),
        "filled_price": round(filled, 4),
        "spread": round(spread, 4),
        "slippage": round(slippage, 4),
        "slippage_pct": round(slippage / expected * 100, 4) if expected else None,
        "commission": round(commission, 4),
        "delay_ms": delay_ms,
        "status": status,
        "version": V110_VERSION,
    }

def execution_stats(limit: int=100) -> Dict[str, Any]:
    init_db()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT slippage, commission, delay_ms, status FROM v110_execution_sim ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return {"ok": True, "count": 0, "fill_rate_pct": None, "avg_slippage": None, "avg_commission": None, "avg_delay_ms": None}
        filled = [r for r in rows if r[3] == "FILLED_SIM"]
        return {
            "ok": True,
            "count": len(rows),
            "fill_rate_pct": round(len(filled)/len(rows)*100, 2),
            "avg_slippage": round(sum(r[0] for r in rows if r[0] is not None)/len(rows), 4),
            "avg_commission": round(sum(r[1] for r in rows if r[1] is not None)/len(rows), 4),
            "avg_delay_ms": round(sum(r[2] for r in rows if r[2] is not None)/len(rows), 2),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
