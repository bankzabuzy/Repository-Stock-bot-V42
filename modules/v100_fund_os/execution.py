
from __future__ import annotations
from typing import Dict, Any
from .broker import get_broker
from .portfolio import portfolio_heat
from .database import audit

def approval_gate(signal_payload: Dict[str, Any]) -> Dict[str, Any]:
    heat = portfolio_heat()
    checks = {
        "portfolio_heat_ok": heat.get("decision") == "ALLOW",
        "signal_not_wait": signal_payload.get("signal") not in {None, "WAIT"},
        "confidence_ok": float(signal_payload.get("confidence",0)) >= 60,
    }
    passed = all(checks.values())
    return {"ok": passed, "checks": checks, "portfolio": heat, "decision": "APPROVED" if passed else "BLOCKED"}

def shadow_order(symbol: str, side: str, qty: float, price: float | None = None) -> Dict[str, Any]:
    audit("SHADOW_ORDER", f"Shadow {side} {qty} {symbol}")
    return {"ok": True, "mode": "SHADOW", "symbol": symbol.upper(), "side": side.upper(), "qty": qty, "price": price, "status": "SHADOW_RECORDED"}

def execute(signal_payload: Dict[str, Any], mode: str = "PAPER") -> Dict[str, Any]:
    gate = approval_gate(signal_payload)
    if not gate.get("ok"):
        return {"ok": False, "execution": "BLOCKED", "gate": gate}
    symbol = signal_payload.get("symbol")
    side = "BUY" if "BUY" in str(signal_payload.get("signal")) else "SELL"
    qty = float(signal_payload.get("qty", 1))
    price = signal_payload.get("price")
    if mode.upper() == "SHADOW":
        return shadow_order(symbol, side, qty, price)
    broker = get_broker("PAPER" if mode.upper()=="PAPER" else None)
    return broker.place_order(symbol, side, qty, price)
