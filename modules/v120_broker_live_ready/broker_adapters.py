
from __future__ import annotations
import os, uuid
from typing import Any, Dict
from .common import V120_VERSION, env_bool, safety_event

class BrokerAdapter:
    name = "BASE"
    asset_classes = []
    def status(self) -> Dict[str, Any]:
        return {"ok": False, "broker": self.name, "connected": False, "message": "not implemented"}
    def place_order(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": False, "broker": self.name, "status": "NOT_IMPLEMENTED"}

class PaperBroker(BrokerAdapter):
    name = "PAPER"
    asset_classes = ["US_STOCK", "ETF", "GOLD_PROXY", "CRYPTO"]
    def status(self) -> Dict[str, Any]:
        return {"ok": True, "broker": self.name, "connected": True, "mode": "PAPER", "message": "paper broker ready"}
    def place_order(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        order_id = "PAPER-" + uuid.uuid4().hex[:12].upper()
        return {
            "ok": True,
            "broker": self.name,
            "status": "ACCEPTED_SIM",
            "order_id": order_id,
            "filled_price": intent.get("limit_price") or intent.get("market_price"),
            "filled_qty": intent.get("qty"),
            "mode": "PAPER",
            "version": V120_VERSION,
        }

class IBKRAdapter(BrokerAdapter):
    name = "IBKR"
    asset_classes = ["US_STOCK", "ETF", "FUTURES", "OPTIONS"]
    def status(self) -> Dict[str, Any]:
        configured = bool(os.getenv("IBKR_HOST") and os.getenv("IBKR_PORT"))
        return {"ok": configured, "broker": self.name, "connected": False, "configured": configured, "message": "IBKR stub-safe; install ib_insync and configure gateway to enable."}
    def place_order(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": False, "broker": self.name, "status": "BLOCKED_STUB", "reason": "IBKR live adapter intentionally disabled until credentials/gateway validation."}

class AlpacaAdapter(BrokerAdapter):
    name = "ALPACA"
    asset_classes = ["US_STOCK", "ETF", "OPTIONS"]
    def status(self) -> Dict[str, Any]:
        configured = bool(os.getenv("ALPACA_API_KEY") and os.getenv("ALPACA_SECRET_KEY"))
        return {"ok": configured, "broker": self.name, "connected": False, "configured": configured, "message": "Alpaca stub-safe; live submit disabled by default."}
    def place_order(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": False, "broker": self.name, "status": "BLOCKED_STUB", "reason": "Alpaca live adapter intentionally disabled until final approval."}

class MT5Adapter(BrokerAdapter):
    name = "MT5"
    asset_classes = ["XAUUSD", "FX", "CFD"]
    def status(self) -> Dict[str, Any]:
        configured = bool(os.getenv("MT5_LOGIN") and os.getenv("MT5_SERVER"))
        return {"ok": configured, "broker": self.name, "connected": False, "configured": configured, "message": "MT5 stub-safe; requires MetaTrader5 package and terminal."}
    def place_order(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": False, "broker": self.name, "status": "BLOCKED_STUB", "reason": "MT5 live adapter intentionally disabled until terminal validation."}

class BinanceAdapter(BrokerAdapter):
    name = "BINANCE"
    asset_classes = ["CRYPTO"]
    def status(self) -> Dict[str, Any]:
        configured = bool(os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET"))
        return {"ok": configured, "broker": self.name, "connected": False, "configured": configured, "message": "Binance stub-safe; live submit disabled by default."}
    def place_order(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": False, "broker": self.name, "status": "BLOCKED_STUB", "reason": "Binance live adapter intentionally disabled until risk review."}

def get_adapter(name: str | None=None) -> BrokerAdapter:
    n = (name or os.getenv("BROKER_DEFAULT", "PAPER")).upper()
    if n == "IBKR": return IBKRAdapter()
    if n == "ALPACA": return AlpacaAdapter()
    if n == "MT5": return MT5Adapter()
    if n == "BINANCE": return BinanceAdapter()
    return PaperBroker()

def all_broker_status() -> Dict[str, Any]:
    adapters = [PaperBroker(), IBKRAdapter(), AlpacaAdapter(), MT5Adapter(), BinanceAdapter()]
    return {"ok": True, "items": [a.status() for a in adapters], "live_enabled": env_bool("ALLOW_LIVE_TRADING")}
