
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, price, safe_float, V430_VERSION

def regime_ai(symbol="SPY"):
    init_db()
    spy = price("SPY")
    qqq = price("QQQ")
    vix = price("^VIX")
    dxy = price("DX-Y.NYB")
    target = price(symbol)

    spyc = safe_float(spy.get("change_pct"),0) or 0
    qqqc = safe_float(qqq.get("change_pct"),0) or 0
    vixc = safe_float(vix.get("change_pct"),0) or 0
    dxyc = safe_float(dxy.get("change_pct"),0) or 0
    tc = safe_float(target.get("change_pct"),0) or 0

    if vixc > 8 or spyc < -2:
        regime = "PANIC"
    elif vixc > 4:
        regime = "HIGH_VOLATILITY"
    elif spyc > 0.5 and qqqc > 0.5 and vixc < 0:
        regime = "RISK_ON"
    elif spyc < -0.5 and dxyc > 0:
        regime = "RISK_OFF"
    elif abs(spyc) < 0.3 and abs(qqqc) < 0.3:
        regime = "SIDEWAY"
    elif abs(tc) > 1:
        regime = "TRENDING"
    else:
        regime = "MIXED"

    mapping = {
        "TRENDING": "Trend Following",
        "SIDEWAY": "Mean Reversion",
        "HIGH_VOLATILITY": "Reduce Size / Wait Confirmation",
        "PANIC": "Capital Protection / Hedge",
        "RISK_ON": "Momentum / Relative Strength",
        "RISK_OFF": "Defensive / Gold Hedge",
        "MIXED": "Selective Only",
    }.get(regime, "Selective Only")
    confidence = 80 if regime in {"PANIC","RISK_ON","RISK_OFF"} else 65 if regime != "MIXED" else 55
    report = {"symbol": symbol, "regime": regime, "strategy_mapping": mapping, "confidence": confidence, "inputs": {"SPY": spy, "QQQ": qqq, "VIX": vix, "DXY": dxy, symbol: target}}
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v430_regime(created_at,symbol,regime,strategy_mapping,confidence,report,model_version) VALUES(?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), symbol.upper(), regime, mapping, confidence, json.dumps(report, ensure_ascii=False, default=str), V430_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V430_VERSION, **report}
