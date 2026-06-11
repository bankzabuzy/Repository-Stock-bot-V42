
from __future__ import annotations
import os
from typing import Any, Dict
from .common import safe_float, env_bool

def classify_asset(symbol: str) -> str:
    s = symbol.upper()
    if s in {"SPY","QQQ","NVDA","AAPL","TSLA","MSFT","META","AMD","TSM"}:
        return "US_STOCK"
    if s in {"XAUUSD","GC=F","GOLD","THAI_GOLD"}:
        return "GOLD_PROXY"
    if s.endswith("USDT") or s in {"BTC","ETH","BTCUSDT","ETHUSDT"}:
        return "CRYPTO"
    return "UNKNOWN"

def pretrade_check(intent: Dict[str, Any]) -> Dict[str, Any]:
    symbol = str(intent.get("symbol","")).upper()
    qty = safe_float(intent.get("qty"), 0) or 0
    notional = abs(qty * (safe_float(intent.get("limit_price"), safe_float(intent.get("market_price"), 0)) or 0))
    max_notional = safe_float(os.getenv("V120_MAX_ORDER_NOTIONAL", "10000"), 10000) or 10000
    checks = {
        "symbol_present": bool(symbol),
        "qty_positive": qty > 0,
        "notional_ok": notional <= max_notional,
        "live_allowed": (str(intent.get("mode","PAPER")).upper() != "LIVE") or env_bool("ALLOW_LIVE_TRADING"),
        "asset_supported": classify_asset(symbol) != "UNKNOWN",
    }
    failed = [k for k,v in checks.items() if not v]
    return {
        "ok": not failed,
        "checks": checks,
        "failed": failed,
        "symbol": symbol,
        "asset_class": classify_asset(symbol),
        "notional": round(notional, 2),
        "max_notional": max_notional,
        "decision": "APPROVED" if not failed else "BLOCKED",
    }
