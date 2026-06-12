import os
from datetime import datetime, timezone, timedelta

VERSION = "V1412_RESTORE_FULL_ANALYSIS_FINAL"

PRIORITY = {
    "US": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "ETF": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "TH": ["SET_API", "THAI_MARKET_API", "YAHOO_BK"],
    "GOLD": ["GOLDTRADERS", "GOLDAPI", "TWELVEDATA_XAUUSD", "YAHOO_GCF"],
    "MACRO": ["FRED", "TRADINGECONOMICS", "ALPHAVANTAGE", "YAHOO"],
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
    "TRADINGECONOMICS": "TRADINGECONOMICS_API_KEY",
}
NO_KEY = {"YAHOO", "YAHOO_BK", "GOLDTRADERS", "YAHOO_GCF"}

def ready(provider):
    if provider == "TWELVEDATA_XAUUSD":
        return bool(os.getenv("TWELVEDATA_API_KEY", "").strip())
    if provider in NO_KEY:
        return True
    env = ENV.get(provider)
    return bool(os.getenv(env, "").strip()) if env else False

def market(symbol):
    s = str(symbol or "").upper().strip()
    if s in {"GOLD","XAU","XAUUSD","GC=F","ทอง","ทองคำ"}:
        return "GOLD"
    if s.endswith(".BK") or s in {"SCB","KBANK","BBL","KTB","PTT","AOT","ADVANC","CPALL","BDMS","PTTEP","DELTA","TRUE"}:
        return "TH"
    if s in {"QQQ","SPY","DIA","IWM","GLD","SLV","XLK","XLF","XLE","XLV","XLY","XLP","TQQQ","SQQQ","SOXL","SOXS"}:
        return "ETF"
    return "US"

def normalize(symbol):
    s = str(symbol or "").upper().strip()
    if s in {"SCB","KBANK","BBL","KTB","PTT","AOT","ADVANC","CPALL","BDMS","PTTEP","DELTA","TRUE"}:
        return s + ".BK"
    if s in {"ทอง","ทองคำ"}:
        return "GOLD"
    return s

def source(mkt):
    for p in PRIORITY.get(mkt, []):
        if ready(p):
            return p
    return "NONE"

def reliability(mkt):
    p = source(mkt)
    if p == "NONE":
        return 0
    providers = PRIORITY.get(mkt, [])
    rank = providers.index(p) + 1 if p in providers else 6
    score = max(55, 100 - (rank-1)*10)
    if p.startswith("YAHOO"):
        score -= 8
    return max(0, min(100, score))

def thai_time_str():
    return (datetime.now(timezone.utc) + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")

def session_info(mkt):
    now_th = datetime.now(timezone.utc) + timedelta(hours=7)
    h = now_th.hour
    if mkt in {"US","ETF"}:
        # rough Thailand time mapping for US market
        if 15 <= h < 20:
            return "PREMARKET", "PREMARKET"
        if 20 <= h or h < 4:
            return "REGULAR/AFTER-HOURS", "LIVE/EXTENDED"
        return "CLOSED_OR_OVERNIGHT", "LAST_CLOSE"
    if mkt == "TH":
        if 10 <= h < 17:
            return "THAI_MARKET_HOURS", "LIVE_OR_DELAYED"
        return "THAI_CLOSED", "LAST_CLOSE"
    if mkt == "GOLD":
        return "GLOBAL_GOLD", "LIVE_OR_LATEST"
    return "LATEST", "LATEST"

def health_text(symbol=None):
    if symbol:
        sym = normalize(symbol)
        mkt = market(sym)
        lines = [f"🔎 API STATUS {sym}", f"Market: {mkt}", f"Current Source: {source(mkt)}", f"Reliability: {reliability(mkt)}/100"]
        for p in PRIORITY.get(mkt, []):
            lines.append(("✅" if ready(p) else "❌") + f" {p} | env={ENV.get(p,'-')}")
    else:
        lines = ["🧭 V1412 API HEALTH"]
        for m in ["US","ETF","TH","GOLD","MACRO"]:
            lines.append(f"{m}: {source(m)} | Reliability {reliability(m)}/100")
    lines.append("")
    lines.append("Priority:")
    lines.append("US/ETF: Webull > Polygon > Finnhub > TwelveData > AlphaVantage > Yahoo")
    lines.append("Thai: SET API > Thai Market API > Yahoo .BK")
    lines.append("Gold: GoldTraders > GoldAPI > XAUUSD TwelveData > GC=F Yahoo")
    lines.append("")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)
