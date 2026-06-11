
from __future__ import annotations
from .common import price

def economic_ai():
    us10y = price("^TNX")
    dxy = price("DX-Y.NYB")
    oil = price("CL=F")
    gold = price("GC=F")
    y = us10y.get("change_pct") or 0
    dx = dxy.get("change_pct") or 0
    oilc = oil.get("change_pct") or 0
    goldc = gold.get("change_pct") or 0

    inflation_pressure = max(0, min(100, 50 + oilc*5 + y*3))
    growth_pressure = max(0, min(100, 50 - max(0,y)*3 - max(0,dx)*3))
    liquidity_pressure = max(0, min(100, 50 - max(0,y)*4 - max(0,dx)*3 + max(0,goldc)*1))

    if inflation_pressure > 70 and growth_pressure < 45:
        regime = "STAGFLATION_RISK"
    elif growth_pressure < 40:
        regime = "RECESSION_FEAR"
    elif inflation_pressure > 70:
        regime = "INFLATION_COMEBACK"
    elif liquidity_pressure > 60:
        regime = "LIQUIDITY_SUPPORT"
    else:
        regime = "MIXED_MACRO"

    return {
        "ok": True,
        "macro_regime": regime,
        "scores": {
            "inflation_pressure": round(inflation_pressure,2),
            "growth_pressure": round(growth_pressure,2),
            "liquidity_pressure": round(liquidity_pressure,2),
        },
        "economic_indicators_supported": ["CPI","Core CPI","PPI","NFP","GDP","ISM","Retail Sales","Unemployment","Consumer Confidence"],
        "proxy_inputs": {"US10Y": us10y, "DXY": dxy, "OIL": oil, "GOLD": gold},
        "note": "ใช้ market proxy แบบฟรีก่อน หากมี API economic calendar จริงสามารถเสียบเพิ่มได้",
    }
