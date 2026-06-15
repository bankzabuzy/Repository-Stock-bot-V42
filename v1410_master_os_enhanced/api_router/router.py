import os
from datetime import datetime, timezone

VERSION = "V1419_MASTER_CLEAN_FINAL"

API_PRIORITY = {
    "US": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "ETF": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "OPTIONS": ["WEBULL", "POLYGON", "YAHOO"],
    "TH": ["SET_API", "THAI_MARKET_API", "YAHOO_BK"],
    "GOLD": ["GOLDTRADERS", "GOLDAPI", "TWELVEDATA_XAUUSD", "YAHOO_GCF"],
    "MACRO": ["FRED", "ALPHAVANTAGE", "YAHOO"],
    "NEWS": ["FINNHUB", "ALPHAVANTAGE", "YAHOO_RSS"],
}

ENV_MAP = {
    "WEBULL": "WEBULL_API_KEY",
    "POLYGON": "POLYGON_API_KEY",
    "FINNHUB": "FINNHUB_API_KEY",
    "TWELVEDATA": "TWELVEDATA_API_KEY",
    "ALPHAVANTAGE": "ALPHAVANTAGE_API_KEY",
    "SET_API": "SET_API_KEY",
    "THAI_MARKET_API": "THAI_MARKET_API_KEY",
    "GOLDAPI": "GOLD_API_KEY",
    "FRED": "FRED_API_KEY",
}

NO_KEY_REQUIRED = {"YAHOO", "YAHOO_BK", "GOLDTRADERS", "YAHOO_GCF", "YAHOO_RSS", "TWELVEDATA_XAUUSD"}

def is_configured(provider):
    if provider in NO_KEY_REQUIRED:
        if provider == "TWELVEDATA_XAUUSD":
            return bool(os.getenv("TWELVEDATA_API_KEY", "").strip())
        return True
    env = ENV_MAP.get(provider)
    return bool(os.getenv(env, "").strip()) if env else False

def provider_status(provider):
    env = ENV_MAP.get(provider, "-")
    ready = is_configured(provider)
    return {
        "provider": provider,
        "env": env,
        "ready": ready,
        "status": "ACTIVE" if ready else "NOT_CONFIGURED"
    }

def best_provider(market):
    for p in API_PRIORITY.get(market, []):
        if is_configured(p):
            return provider_status(p)
    return {"provider": "NONE", "env": "-", "ready": False, "status": "NO_PROVIDER_READY"}

def reliability_score(market):
    priorities = API_PRIORITY.get(market, [])
    if not priorities:
        return 0
    best = best_provider(market)["provider"]
    if best == "NONE":
        return 0
    rank = priorities.index(best) + 1
    base = max(50, 100 - (rank-1)*10)
    if best.startswith("YAHOO"):
        base -= 8
    return max(0, min(100, base))

def market_from_symbol(symbol):
    s = str(symbol or "").upper().strip()
    if s in {"GOLD", "XAUUSD", "XAU", "ทอง", "ทองคำ"}:
        return "GOLD"
    if s.endswith(".BK") or s in {"SCB","KBANK","BBL","KTB","PTT","AOT","ADVANC","CPALL","BDMS","PTTEP","DELTA","TRUE"}:
        return "TH"
    if s in {"SPY","QQQ","DIA","IWM","GLD","SLV","XLK","XLF","XLE","XLV","XLY","XLP","TQQQ","SQQQ","SOXL","SOXS"}:
        return "ETF"
    return "US"

def api_status_text(symbol=None):
    if symbol:
        market = market_from_symbol(symbol)
        lines = [f"🔎 API STATUS: {symbol}", f"Market: {market}"]
        lines.append(f"Current Source: {best_provider(market)['provider']}")
        lines.append(f"Reliability Score: {reliability_score(market)}/100")
        lines.append("")
        for p in API_PRIORITY.get(market, []):
            st = provider_status(p)
            icon = "✅" if st["ready"] else "❌"
            lines.append(f"{icon} {p} | {st['status']} | env={st['env']}")
    else:
        lines = ["🧭 V1410 API ROUTER STATUS"]
        for market in ["US","ETF","OPTIONS","TH","GOLD","MACRO","NEWS"]:
            best = best_provider(market)
            lines.append(f"{market}: {best['provider']} | {best['status']} | Reliability {reliability_score(market)}/100")
    lines.append("")
    lines.append("Priority:")
    lines.append("US/ETF: Webull > Polygon > Finnhub > TwelveData > AlphaVantage > Yahoo")
    lines.append("Options: Webull > Polygon > Yahoo")
    lines.append("Thai: SET API > Thai Market API > Yahoo .BK")
    lines.append("Gold: GoldTraders > GoldAPI > XAUUSD TwelveData > GC=F Yahoo")
    lines.append("")
    lines.append("Version : V1410_MASTER_OS_ENHANCED")
    return "\n".join(lines)

def price_source_note(symbol):
    market = market_from_symbol(symbol)
    best = best_provider(market)
    return {
        "market": market,
        "source": best["provider"],
        "reliability": reliability_score(market),
        "session_note": "Pre-market/After-hours ใช้ Webull/Polygon ก่อน หากไม่มีใช้ fallback",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
