
from __future__ import annotations
from datetime import datetime, timezone
import json
from .common import init_db, connect, safe_float, price, V550_VERSION

def order_dry_run(symbol="SPY", side="BUY", qty=1, broker="WEBULL"):
    init_db()
    qty = safe_float(qty, 1) or 1
    snap = price(symbol)
    px = safe_float(snap.get("price"), 100) or 100
    notional = abs(px * qty)
    slippage = max(0.01, px * 0.0008)
    commission = 0.00 if broker.upper() in {"WEBULL","PAPER"} else max(1.0, notional * 0.0001)
    max_notional = 10000
    status = "PASS_DRY_RUN" if notional <= max_notional else "BLOCK_NOTIONAL_TOO_HIGH"
    report = {
        "symbol": symbol.upper(), "side": side.upper(), "qty": qty, "broker": broker.upper(),
        "estimated_price": px, "estimated_slippage": round(slippage, 4),
        "estimated_commission": round(commission, 4), "notional": round(notional,2),
        "status": status, "snapshot": snap,
        "note": "Dry run only. No real order is sent.",
    }
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v550_order_dryrun(created_at,broker,symbol,side,qty,estimated_price,estimated_slippage,estimated_commission,notional,status,report,model_version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), broker.upper(), symbol.upper(), side.upper(), qty, px, slippage, commission, notional, status, json.dumps(report, ensure_ascii=False, default=str), V550_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V550_VERSION, **report}
