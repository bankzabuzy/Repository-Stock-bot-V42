
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from .common import init_db, connect, safe_float, price, V390_VERSION

def kelly_fraction(winrate: float, payoff: float):
    p = winrate
    q = 1 - p
    b = payoff
    if b <= 0:
        return 0
    return max(0, min(0.25, (b*p - q)/b))

def position_sizing(symbol="SPY", equity=100000, base_risk_pct=1.0, winrate=0.55, payoff=1.5, volatility=0.18, method="HYBRID"):
    init_db()
    equity = safe_float(equity, 100000) or 100000
    base = safe_float(base_risk_pct, 1.0) or 1.0
    wr = safe_float(winrate, 0.55) or 0.55
    pf = safe_float(payoff, 1.5) or 1.5
    vol = safe_float(volatility, 0.18) or 0.18
    snap = price(symbol)
    px = safe_float(snap.get("price"), 100) or 100

    kelly = kelly_fraction(wr, pf) * 100
    vol_target = max(0.1, min(base, base * (0.18 / max(0.05, vol))))
    hybrid_risk = min(base, kelly, vol_target)
    if method.upper() == "KELLY":
        suggested_risk = kelly
    elif method.upper() == "VOL_TARGET":
        suggested_risk = vol_target
    else:
        suggested_risk = hybrid_risk
    risk_amount = equity * suggested_risk / 100
    stop_distance = px * 0.03
    qty = risk_amount / stop_distance if stop_distance else 0
    report = {
        "symbol": symbol, "method": method, "equity": equity, "price": px,
        "kelly_pct": round(kelly, 3), "vol_target_pct": round(vol_target, 3),
        "suggested_risk_pct": round(suggested_risk, 3),
        "suggested_qty": round(qty, 4),
        "reason": "risk = min(base, Kelly, volatility target) for capital survival",
    }
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v390_position_sizing(created_at,symbol,method,base_risk,volatility,winrate,payoff,suggested_risk,suggested_qty,report,model_version) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), symbol.upper(), method.upper(), base, vol, wr, pf, suggested_risk, qty, json.dumps(report, ensure_ascii=False, default=str), V390_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V390_VERSION, **report}
