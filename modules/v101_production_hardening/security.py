
from __future__ import annotations
import os, hashlib, hmac, time
from typing import Dict, Any

V101_VERSION = "V101_PRODUCTION_HARDENING_SECURITY_STABLE"

def is_admin_token_set() -> bool:
    return bool(os.getenv("ADMIN_TOKEN"))

def verify_admin_token(token: str | None) -> Dict[str, Any]:
    expected = os.getenv("ADMIN_TOKEN", "")
    if not expected:
        return {"ok": False, "reason": "ADMIN_TOKEN_NOT_SET", "safe_mode": True}
    ok = hmac.compare_digest(str(token or ""), expected)
    return {"ok": ok, "reason": "OK" if ok else "INVALID_TOKEN", "safe_mode": not ok}

def safe_public_config() -> Dict[str, Any]:
    keys = [
        "ADMIN_TOKEN",
        "LINE_CHANNEL_ACCESS_TOKEN",
        "LINE_CHANNEL_SECRET",
        "FINNHUB_API_KEY",
        "ALPHAVANTAGE_API_KEY",
        "FMP_API_KEY",
        "TWELVEDATA_API_KEY",
        "DATABASE_URL",
        "DB_PATH",
        "ALLOW_LIVE_TRADING",
        "FUND_MODE",
    ]
    return {
        "version": V101_VERSION,
        "env_present": {k: bool(os.getenv(k)) for k in keys},
        "live_trading_enabled": os.getenv("ALLOW_LIVE_TRADING", "false").lower() in {"1","true","yes"},
        "fund_mode": os.getenv("FUND_MODE", "PAPER"),
        "note": "ไม่แสดงค่า secret จริง แสดงเฉพาะว่ามีหรือไม่มี",
    }

def request_signature(text: str) -> str:
    secret = os.getenv("ADMIN_TOKEN", "local")
    return hashlib.sha256((secret + text).encode("utf-8")).hexdigest()[:16]
