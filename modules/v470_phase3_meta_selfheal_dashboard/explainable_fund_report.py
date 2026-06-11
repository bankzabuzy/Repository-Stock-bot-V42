
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, price, safe_float, V470_VERSION

def _phase2(symbol):
    try:
        from modules.v430_phase2_market_intelligence.dashboard import phase2_center
        return phase2_center(symbol)
    except Exception as e:
        return {"ok": False, "error": str(e)}

def explainable_fund_report(symbol="SPY"):
    init_db()
    snap = price(symbol)
    p2 = _phase2(symbol)
    debate = p2.get("debate", {})
    regime = p2.get("regime", {})
    micro = p2.get("microstructure", {})
    decision = debate.get("final_decision", "WAIT")
    why_buy = []
    why_sell = []
    why_wait = []
    if micro.get("order_flow_bias") == "BUY_PRESSURE":
        why_buy.append("Order-flow proxy เป็นฝั่งซื้อ")
    if regime.get("regime") in {"RISK_ON", "TRENDING"}:
        why_buy.append(f"Regime {regime.get('regime')} เหมาะกับ {regime.get('strategy_mapping')}")
    if micro.get("order_flow_bias") == "SELL_PRESSURE":
        why_sell.append("Order-flow proxy เป็นฝั่งขาย")
    if regime.get("regime") in {"RISK_OFF", "PANIC", "HIGH_VOLATILITY"}:
        why_wait.append(f"Regime {regime.get('regime')} ต้องลดความเสี่ยง")
    if debate.get("consensus_score", 0) < 80:
        why_wait.append("AI consensus ยังไม่สูงพอ")
    if p2.get("digital_twin", {}).get("decision") == "BLOCK_LIVE_EXECUTION":
        why_wait.append("Digital Twin safety gate ไม่ผ่าน")
    risk = "ลดขนาดไม้ถ้า volatility สูง หรือ consensus ต่ำกว่า 80%"
    report = {
        "symbol": symbol,
        "decision": decision,
        "why_buy": why_buy,
        "why_sell": why_sell,
        "why_wait": why_wait,
        "risk_explanation": risk,
        "snapshot": snap,
        "phase2": p2,
    }
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v470_fund_reports(created_at,symbol,decision,why_buy,why_sell,why_wait,risk_explanation,report,model_version) VALUES(?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), symbol.upper(), decision, " | ".join(why_buy), " | ".join(why_sell), " | ".join(why_wait), risk, json.dumps(report, ensure_ascii=False, default=str), V470_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V470_VERSION, **report}
