import os
from datetime import datetime, timezone

VERSION = "V1419_MASTER_CLEAN_FINAL"

PRIORITY = {
    "US": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "ETF": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "CALL": ["WEBULL", "POLYGON", "FINNHUB", "YAHOO"],
    "PUT": ["WEBULL", "POLYGON", "FINNHUB", "YAHOO"],
    "TH": ["SET_API", "THAI_MARKET_API", "YAHOO_BK"],
    "GOLD": ["GOLDTRADERS", "GOLDAPI", "TWELVEDATA_XAUUSD", "YAHOO_GCF"],
    "MACRO": ["FRED", "ALPHAVANTAGE", "YAHOO"],
    "NEWS": ["FINNHUB", "ALPHAVANTAGE", "YAHOO_RSS"],
}

ENV = {
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

NO_KEY = {"YAHOO", "YAHOO_BK", "GOLDTRADERS", "YAHOO_GCF", "YAHOO_RSS"}

def is_ready(provider):
    if provider == "TWELVEDATA_XAUUSD":
        return bool(os.getenv("TWELVEDATA_API_KEY", "").strip())
    if provider in NO_KEY:
        return True
    key = ENV.get(provider)
    return bool(os.getenv(key, "").strip()) if key else False

def classify(symbol):
    s = str(symbol or "").upper().strip()
    if s in {"GOLD", "XAUUSD", "XAU", "ทอง", "ทองคำ", "GC=F"}:
        return "GOLD"
    if s.endswith(".BK") or s in {"SCB","KBANK","BBL","KTB","PTT","AOT","ADVANC","CPALL","BDMS","PTTEP","DELTA","TRUE"}:
        return "TH"
    if s in {"SPY","QQQ","DIA","IWM","GLD","SLV","XLK","XLF","XLE","XLV","XLY","XLP","TQQQ","SQQQ","SOXL","SOXS"}:
        return "ETF"
    return "US"

def normalize_symbol(symbol):
    s = str(symbol or "").upper().strip()
    if s in {"SCB","KBANK","BBL","KTB","PTT","AOT","ADVANC","CPALL","BDMS","PTTEP","DELTA","TRUE"}:
        return s + ".BK"
    return s

def best_provider(market):
    for p in PRIORITY.get(market, []):
        if is_ready(p):
            return p
    return "NONE"

def reliability(market):
    providers = PRIORITY.get(market, [])
    p = best_provider(market)
    if p == "NONE":
        return 0
    rank = providers.index(p) + 1
    score = max(50, 100 - (rank-1)*10)
    if p.startswith("YAHOO"):
        score -= 8
    return max(0, min(100, score))

def session_label(market):
    if market in {"US","ETF","CALL","PUT"}:
        return "AUTO_SESSION: Prev Close / Pre-market / Regular / After-hours"
    if market == "TH":
        return "SET_LAST_CLOSE / Yahoo .BK fallback"
    if market == "GOLD":
        return "GoldTraders / GoldAPI / XAUUSD fallback"
    return "Macro latest available"

def status(symbol=None):
    if symbol:
        sym = normalize_symbol(symbol)
        market = classify(sym)
        title = f"🔎 DATA STATUS: {sym}"
    else:
        sym = None
        market = None
        title = "🧭 V1411 API HEALTH"
    lines = [title]
    if market:
        lines.append(f"Market: {market}")
        lines.append(f"Current Source: {best_provider(market)}")
        lines.append(f"Reliability: {reliability(market)}/100")
        lines.append(f"Session: {session_label(market)}")
        lines.append("")
        for p in PRIORITY.get(market, []):
            icon = "✅" if is_ready(p) else "❌"
            lines.append(f"{icon} {p} | env={ENV.get(p, '-')}")
    else:
        for m in ["US","ETF","CALL","PUT","TH","GOLD","MACRO","NEWS"]:
            lines.append(f"{m}: {best_provider(m)} | Reliability {reliability(m)}/100")
    lines.append("")
    lines.append("Priority:")
    lines.append("US/ETF/Options: Webull > Polygon > Finnhub > TwelveData > AlphaVantage > Yahoo")
    lines.append("Thai: SET API > Thai Market API > Yahoo .BK")
    lines.append("Gold: GoldTraders > GoldAPI > XAUUSD TwelveData > GC=F Yahoo")
    lines.append("Macro: FRED > AlphaVantage > Yahoo")
    lines.append("")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)
