
from __future__ import annotations
from .common import price

WATCH = {"SPY":"SP500","QQQ":"NASDAQ","^VIX":"VIX","DX-Y.NYB":"DXY","^TNX":"US10Y","GC=F":"GOLD","CL=F":"OIL","BTC-USD":"BTC"}

def global_capital_flow():
    data = {name: price(sym) for sym, name in WATCH.items()}
    ch = {name: (snap.get("change_pct") or 0) for name, snap in data.items()}
    flows = []
    if ch.get("SP500",0) > 0 and ch.get("NASDAQ",0) > 0 and ch.get("VIX",0) < 0:
        flows.append("Risk assets inflow")
    if ch.get("GOLD",0) > 0 and ch.get("DXY",0) > 0:
        flows.append("Safe haven / geopolitical hedge")
    if ch.get("DXY",0) > 0 and ch.get("US10Y",0) > 0:
        flows.append("USD/Yield tightening pressure")
    if ch.get("BTC",0) > 2:
        flows.append("Speculative crypto flow")
    regime = "RISK_ON" if "Risk assets inflow" in flows else "RISK_OFF" if "USD/Yield tightening pressure" in flows else "MIXED"
    return {"ok": True, "regime": regime, "flows": flows or ["Mixed/unclear flow"], "changes": ch, "data": data}

def regime_switching():
    flow = global_capital_flow()
    regime = flow.get("regime")
    if regime == "RISK_ON":
        allocation_bias = {"ETF": "ADD", "US_STOCK": "ADD_SELECTIVE", "GOLD": "HOLD", "CASH": "REDUCE_SLIGHTLY"}
    elif regime == "RISK_OFF":
        allocation_bias = {"ETF": "REDUCE", "US_STOCK": "REDUCE", "GOLD": "ADD_HEDGE", "CASH": "ADD"}
    else:
        allocation_bias = {"ETF": "HOLD", "US_STOCK": "SELECTIVE", "GOLD": "HOLD", "CASH": "HOLD"}
    return {"ok": True, "regime": regime, "allocation_bias": allocation_bias, "flow": flow}
