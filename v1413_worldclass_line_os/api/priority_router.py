import os
from datetime import datetime, timezone, timedelta

VERSION = "V1413_WORLDCLASS_LINE_OS_FINAL"

PRIORITY = {
    "US": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "ETF": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "TH": ["SET_API", "THAI_MARKET_API", "YAHOO_BK"],
    "GOLD": ["GOLDTRADERS_PUBLIC", "GOLDAPI", "TWELVEDATA_XAUUSD", "YAHOO_GCF"],
    "MACRO": ["FRED", "TRADINGECONOMICS", "ALPHAVANTAGE", "YAHOO"],
    "NEWS": ["FINNHUB", "TRADINGECONOMICS", "YAHOO_RSS"],
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
PUBLIC = {"YAHOO", "YAHOO_BK", "GOLDTRADERS_PUBLIC", "YAHOO_GCF", "YAHOO_RSS"}

def env_ready(provider: str) -> bool:
    if provider == "TWELVEDATA_XAUUSD":
        return bool(os.getenv("TWELVEDATA_API_KEY", "").strip())
    if provider in PUBLIC:
        return True
    key = ENV.get(provider)
    return bool(os.getenv(key, "").strip()) if key else False

def normalize_symbol(symbol: str) -> str:
    s = (symbol or "").strip().upper()
    if s in {"ทอง", "ทองคำ", "XAU", "XAUUSD", "GC=F"}:
        return "GOLD"
    thai = {"SCB","KBANK","BBL","KTB","PTT","AOT","ADVANC","CPALL","BDMS","PTTEP","DELTA","TRUE"}
    if s in thai:
        return s + ".BK"
    return s

def market_of(symbol: str) -> str:
    s = normalize_symbol(symbol)
    if s == "GOLD":
        return "GOLD"
    if s.endswith(".BK"):
        return "TH"
    if s in {"QQQ","SPY","DIA","IWM","GLD","SLV","XLK","XLF","XLE","XLV","XLY","XLP","TQQQ","SQQQ","SOXL","SOXS"}:
        return "ETF"
    return "US"

def primary_source(market: str) -> str:
    for p in PRIORITY.get(market, []):
        if env_ready(p):
            return p
    return "NONE"

def reliability(market: str) -> int:
    p = primary_source(market)
    if p == "NONE":
        return 0
    providers = PRIORITY.get(market, [])
    rank = providers.index(p) + 1 if p in providers else 6
    score = max(55, 100 - (rank - 1) * 10)
    if p.startswith("YAHOO"):
        score -= 8
    return max(0, min(100, score))

def now_th() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=7)

def time_th() -> str:
    return now_th().strftime("%d/%m/%Y %H:%M")

def session_of(market: str):
    h = now_th().hour
    if market in {"US","ETF"}:
        if 15 <= h < 20:
            return "PREMARKET", "ใช้ราคา Pre-market เป็นหลักเมื่อมีข้อมูล"
        if 20 <= h or h < 4:
            return "US OPEN/EXT", "ใช้ราคา Regular/After-hours ตามเวลาตลาด"
        return "CLOSED", "ตลาดปิด ใช้ราคาปิดล่าสุด + Pre/After เป็นข้อมูลประกอบ"
    if market == "TH":
        if 10 <= h < 17:
            return "TH OPEN", "หุ้นไทยอาจมีดีเลย์ตามแหล่งข้อมูล"
        return "TH CLOSED", "ตลาดไทยปิด ใช้ราคาปิดล่าสุด"
    if market == "GOLD":
        return "GOLD LIVE", "ทองใช้ราคาสมาคมค้าทองคำเป็นหลัก"
    return "LATEST", "ข้อมูลล่าสุด"

def api_health(symbol=None) -> str:
    if symbol:
        sym = normalize_symbol(symbol)
        m = market_of(sym)
        lines = [f"🧭 สถานะข้อมูล {sym}", f"ตลาด: {m}", f"แหล่งหลัก: {primary_source(m)} | {reliability(m)}/100"]
        for p in PRIORITY.get(m, []):
            lines.append(("✅" if env_ready(p) else "❌") + f" {p}")
    else:
        lines = ["🧭 SYSTEM HEALTH V1413"]
        for m in ["US","ETF","TH","GOLD","MACRO","NEWS"]:
            lines.append(f"{m}: {primary_source(m)} | {reliability(m)}/100")
        lines.append("")
        lines.append("Gold Priority: สมาคมค้าทองคำ > GoldAPI > XAUUSD > GC=F")
    lines.append("")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)
