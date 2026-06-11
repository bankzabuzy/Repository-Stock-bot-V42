
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any
from .config import get_config, V100_VERSION
from .database import init_db, connect, audit

class BrokerAdapter:
    name = "BASE"
    def place_order(self, symbol: str, side: str, qty: float, price: float | None = None) -> Dict[str, Any]:
        raise NotImplementedError

class PaperBroker(BrokerAdapter):
    name = "PAPER"
    def place_order(self, symbol: str, side: str, qty: float, price: float | None = None) -> Dict[str, Any]:
        init_db()
        try:
            conn = connect()
            cur = conn.cursor()
            order_id = f"PAPER-{int(datetime.now(timezone.utc).timestamp())}"
            cur.execute(
                "INSERT INTO fund_executions(created_at,broker,mode,symbol,side,qty,price,status,order_id,model_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), self.name, "PAPER", symbol.upper(), side.upper(), qty, price, "FILLED_SIM", order_id, V100_VERSION)
            )
            conn.commit()
            conn.close()
            audit("ORDER", f"Paper order {side} {qty} {symbol}", severity="INFO")
            return {"ok": True, "broker": self.name, "mode": "PAPER", "order_id": order_id, "status": "FILLED_SIM"}
        except Exception as e:
            return {"ok": False, "broker": self.name, "error": str(e)}

class StubBroker(BrokerAdapter):
    def __init__(self, name: str):
        self.name = name
    def place_order(self, symbol: str, side: str, qty: float, price: float | None = None) -> Dict[str, Any]:
        cfg = get_config()
        if not cfg.allow_live_trading:
            return {
                "ok": False,
                "broker": self.name,
                "status": "BLOCKED",
                "reason": "Live trading disabled. Set ALLOW_LIVE_TRADING=true only after full validation.",
            }
        return {"ok": False, "broker": self.name, "status": "NOT_CONNECTED", "reason": "API credentials/SDK not configured"}

def get_broker(name: str | None = None) -> BrokerAdapter:
    n = (name or get_config().broker_default or "PAPER").upper()
    if n == "PAPER":
        return PaperBroker()
    if n in {"IBKR", "ALPACA", "MT5", "BINANCE"}:
        return StubBroker(n)
    return PaperBroker()

def broker_status() -> Dict[str, Any]:
    cfg = get_config()
    return {
        "ok": True,
        "default": cfg.broker_default,
        "mode": cfg.mode,
        "allow_live_trading": cfg.allow_live_trading,
        "supported": ["PAPER", "IBKR", "ALPACA", "MT5", "BINANCE"],
        "live_note": "IBKR/Alpaca/MT5/Binance are stub-safe until credentials and SDK are configured.",
    }
