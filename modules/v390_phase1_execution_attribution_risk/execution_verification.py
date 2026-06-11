
from __future__ import annotations
import json, random
from datetime import datetime, timezone
from .common import init_db, connect, safe_float, price, V390_VERSION

def verify_execution(symbol="SPY", side="BUY", expected_price=None, qty=1, broker="PAPER"):
    init_db()
    snap = price(symbol)
    expected = safe_float(expected_price, snap.get("price") or 100) or 100
    qty = safe_float(qty, 1) or 1
    # PAPER verification simulation for proof layer; live adapters remain guarded in V220
    latency_ms = round(random.uniform(80, 950), 2)
    spread = expected * random.uniform(0.0001, 0.0015)
    filled = expected + spread if side.upper() == "BUY" else expected - spread
    slippage = filled - expected
    partial_fill = 0 if qty <= 100 else 1
    status = "VERIFIED_FILLED_SIM" if broker.upper() == "PAPER" else "SAFE_STUB_NOT_SENT"
    reject = None if broker.upper() == "PAPER" else "live broker disabled until credential validation"
    report = {
        "symbol": symbol, "side": side.upper(), "broker": broker.upper(),
        "expected_price": expected, "filled_price": filled, "qty": qty,
        "status": status, "partial_fill": bool(partial_fill),
        "slippage": slippage, "latency_ms": latency_ms, "source_price": snap,
    }
    conn = connect(); cur = conn.cursor()
    cur.execute("""INSERT INTO v390_execution_verification(created_at,broker,symbol,side,expected_price,filled_price,qty,status,broker_reject_reason,partial_fill,slippage,latency_ms,report,model_version)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (datetime.now(timezone.utc).isoformat(), broker.upper(), symbol.upper(), side.upper(), expected, filled, qty, status, reject, partial_fill, slippage, latency_ms, json.dumps(report, ensure_ascii=False, default=str), V390_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V390_VERSION, **report}

def execution_verification_status():
    init_db()
    sample = verify_execution("SPY", "BUY", None, 1, "PAPER")
    conn = connect(); conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM v390_execution_verification ORDER BY id DESC LIMIT 20")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"ok": True, "latest_sample": sample, "recent": rows}
