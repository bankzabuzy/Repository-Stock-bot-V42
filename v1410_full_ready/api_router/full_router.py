import os
from datetime import datetime, timezone

VERSION = "V1410_FULL_READY_LINE_COMMANDS_FIXED"

API_PRIORITY = {
    "US": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "ETF": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "CALL": ["WEBULL", "POLYGON", "FINNHUB", "YAHOO"],
    "PUT": ["WEBULL", "POLYGON", "FINNHUB", "YAHOO"],
    "TH": ["SET_API", "THAI_MARKET_API", "YAHOO_BK"],
    "GOLD": ["GOLDTRADERS", "GOLDAPI", "TWELVEDATA_XAUUSD", "YAHOO_GCF"],
    "MACRO": ["FRED", "ALPHAVANTAGE", "YAHOO"],
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
NO_KEY = {"YAHOO", "YAHOO_BK", "GOLDTRADERS", "YAHOO_GCF"}

def ready(provider):
    if provider == "TWELVEDATA_XAUUSD":
        return bool(os.getenv("TWELVEDATA_API_KEY", "").strip())
    if provider in NO_KEY:
        return True
    env = ENV_MAP.get(provider)
    return bool(os.getenv(env, "").strip()) if env else False

def best(market):
    for p in API_PRIORITY.get(market, []):
        if ready(p):
            return p
    return "NONE"

def reliability(market):
    providers = API_PRIORITY.get(market, [])
    p = best(market)
    if p == "NONE":
        return 0
    rank = providers.index(p) + 1
    score = max(55, 100 - (rank - 1) * 10)
    if p.startswith("YAHOO"):
        score -= 8
    return max(0, min(100, score))

def session_note(market):
    if market in {"US", "ETF", "CALL", "PUT"}:
        return "รองรับ Prev Close / Pre-market / Regular / After-hours ตาม source ที่พร้อม"
    if market == "TH":
        return "หุ้นไทยใช้ SET/Thai API ก่อน ถ้าไม่มีใช้ Yahoo .BK เป็น fallback"
    if market == "GOLD":
        return "ทองใช้ GoldTraders/GoldAPI/XAUUSD ตามลำดับ"
    return "ใช้ macro source ตามลำดับ"

def status_text(symbol=None, market=None):
    if symbol and not market:
        s = symbol.upper()
        if s.endswith(".BK") or s in {"SCB","KBANK","BBL","KTB","PTT","AOT","ADVANC"}:
            market = "TH"
        elif s in {"GOLD","XAUUSD","XAU","ทอง","ทองคำ"}:
            market = "GOLD"
        elif s in {"SPY","QQQ","DIA","IWM","GLD","XLK","XLF"}:
            market = "ETF"
        else:
            market = "US"
    market = market or "US"
    lines = [f"🔎 API STATUS {symbol or market}", f"Market: {market}", f"Current Source: {best(market)}", f"Reliability: {reliability(market)}/100", ""]
    for p in API_PRIORITY.get(market, []):
        icon = "✅" if ready(p) else "❌"
        env = ENV_MAP.get(p, "-")
        lines.append(f"{icon} {p} | env={env}")
    lines.append("")
    lines.append("Priority:")
    lines.append("US/ETF/Options: Webull > Polygon > Finnhub > TwelveData > AlphaVantage > Yahoo")
    lines.append("Thai: SET API > Thai Market API > Yahoo .BK")
    lines.append("Gold: GoldTraders > GoldAPI > XAUUSD TwelveData > GC=F Yahoo")
    lines.append("")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)

def source_block(symbol, market):
    return f"Source: {best(market)} | Reliability {reliability(market)}/100 | {session_note(market)}"
