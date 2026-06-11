
from __future__ import annotations
import os
from datetime import datetime, timezone
from .common import init_db, connect, safe_float, price, V230_VERSION

ASSET_CLASS = {
    "SPY":"ETF", "QQQ":"ETF", "NVDA":"US_STOCK", "AAPL":"US_STOCK", "MSFT":"US_STOCK",
    "TSM":"US_STOCK", "AMD":"US_STOCK", "TSLA":"US_STOCK",
    "GC=F":"GOLD", "XAUUSD":"GOLD", "THAI_GOLD":"GOLD",
    "BTCUSDT":"CRYPTO", "ETHUSDT":"CRYPTO", "BTC":"CRYPTO", "ETH":"CRYPTO",
    "CASH":"CASH"
}

def seed_positions_from_env():
    init_db()
    raw = os.getenv("V230_POSITIONS", os.getenv("V200_POSITIONS", "SPY:10:500,QQQ:5:450,NVDA:3:900,GC=F:1:2300,CASH:20000:1"))
    conn = connect(); cur = conn.cursor()
    for part in raw.split(","):
        bits = part.split(":")
        if len(bits) >= 3:
            sym = bits[0].strip().upper()
            qty = safe_float(bits[1], 0) or 0
            avg = safe_float(bits[2], 0) or 0
            last = avg if sym == "CASH" else (price(sym).get("price") or avg)
            mv = qty * last
            unreal = (last - avg) * qty
            cur.execute("""
                INSERT OR IGNORE INTO v230_live_positions(symbol,asset_class,qty,avg_price,last_price,market_value,unrealized_pnl,realized_pnl,risk_bucket,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
            """, (sym, ASSET_CLASS.get(sym,"OTHER"), qty, avg, last, mv, unreal, 0, "CORE" if sym in {"SPY","QQQ","CASH"} else "TACTICAL", datetime.now(timezone.utc).isoformat()))
    conn.commit(); conn.close()
    return {"ok": True}

def refresh_positions():
    seed_positions_from_env()
    conn = connect(); conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM v230_live_positions")
    rows = [dict(r) for r in cur.fetchall()]
    updated = []
    for r in rows:
        sym = r["symbol"]
        last = r["last_price"] if sym == "CASH" else (price(sym).get("price") or r["last_price"])
        mv = (r["qty"] or 0) * (last or 0)
        unreal = ((last or 0) - (r["avg_price"] or 0)) * (r["qty"] or 0)
        cur.execute("UPDATE v230_live_positions SET last_price=?, market_value=?, unrealized_pnl=?, updated_at=? WHERE symbol=?",
                    (last, mv, unreal, datetime.now(timezone.utc).isoformat(), sym))
        r.update({"last_price": last, "market_value": mv, "unrealized_pnl": unreal})
        updated.append(r)
    conn.commit(); conn.close()
    return {"ok": True, "positions": updated}

def portfolio_snapshot():
    data = refresh_positions()
    positions = data.get("positions", [])
    total_mv = sum(float(p.get("market_value") or 0) for p in positions)
    total_unreal = sum(float(p.get("unrealized_pnl") or 0) for p in positions)
    for p in positions:
        p["weight_pct"] = round((float(p.get("market_value") or 0) / total_mv * 100), 2) if total_mv else 0
    exposure = {}
    for p in positions:
        ac = p.get("asset_class") or "OTHER"
        exposure[ac] = round(exposure.get(ac, 0) + p.get("weight_pct", 0), 2)
    heat = round(100 - exposure.get("CASH", 0), 2)
    return {"ok": True, "version": V230_VERSION, "total_market_value": round(total_mv,2), "total_unrealized_pnl": round(total_unreal,2), "heat": heat, "exposure": exposure, "positions": positions}
