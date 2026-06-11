
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, price, safe_float, V430_VERSION

def market_microstructure(symbol="SPY"):
    init_db()
    snap = price(symbol)
    chg = safe_float(snap.get("change_pct"), 0) or 0
    px_ok = bool(snap.get("ok"))
    liquidity = 80 if px_ok and symbol.upper() in {"SPY","QQQ","NVDA","AAPL","MSFT"} else 60 if px_ok else 35
    absorption = max(0, min(100, 50 + abs(chg)*5))
    stop_hunt = max(0, min(100, 45 + abs(chg)*8 if abs(chg) > 1.2 else 35))
    fake_breakout = max(0, min(100, 40 + abs(chg)*6 if 0.7 < abs(chg) < 1.8 else 30))
    spoofing = max(0, min(100, 25 + abs(chg)*4))
    if chg > 0.4 and liquidity >= 70:
        bias = "BUY_PRESSURE"
    elif chg < -0.4:
        bias = "SELL_PRESSURE"
    else:
        bias = "NEUTRAL_FLOW"
    report = {
        "symbol": symbol, "snapshot": snap, "liquidity_score": liquidity,
        "absorption_score": round(absorption,2), "stop_hunt_score": round(stop_hunt,2),
        "fake_breakout_score": round(fake_breakout,2), "spoofing_score": round(spoofing,2),
        "order_flow_bias": bias,
        "note": "free-data proxy; replace with real L2/orderbook feed when available",
    }
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v430_microstructure(created_at,symbol,liquidity_score,absorption_score,stop_hunt_score,fake_breakout_score,spoofing_score,order_flow_bias,report,model_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), symbol.upper(), liquidity, absorption, stop_hunt, fake_breakout, spoofing, bias, json.dumps(report, ensure_ascii=False, default=str), V430_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V430_VERSION, **report}
