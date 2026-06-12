import os
from datetime import datetime, timezone, timedelta

VERSION = "V1412.1_CLEAN_LINE_GOLDTRADERS_FINAL"

PRIORITY = {
    "US": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "ETF": ["WEBULL", "POLYGON", "FINNHUB", "TWELVEDATA", "ALPHAVANTAGE", "YAHOO"],
    "TH": ["SET_API", "THAI_MARKET_API", "YAHOO_BK"],
    "GOLD": ["GOLDTRADERS_PUBLIC", "GOLDAPI", "TWELVEDATA_XAUUSD", "YAHOO_GCF"],
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
NO_KEY = {"YAHOO", "YAHOO_BK", "GOLDTRADERS_PUBLIC", "YAHOO_GCF"}

def ready(provider):
    if provider == "TWELVEDATA_XAUUSD":
        return bool(os.getenv("TWELVEDATA_API_KEY", "").strip())
    if provider in NO_KEY:
        return True
    env = ENV.get(provider)
    return bool(os.getenv(env, "").strip()) if env else False

def normalize(symbol):
    s = str(symbol or "").strip().upper()
    if s in {"SCB","KBANK","BBL","KTB","PTT","AOT","ADVANC","CPALL","BDMS","PTTEP","DELTA","TRUE"}:
        return s + ".BK"
    if s in {"ทอง","ทองคำ","XAU","XAUUSD","GC=F"}:
        return "GOLD"
    return s

def market(symbol):
    s = normalize(symbol)
    if s == "GOLD":
        return "GOLD"
    if s.endswith(".BK"):
        return "TH"
    if s in {"QQQ","SPY","DIA","IWM","GLD","SLV","XLK","XLF","XLE","XLV","TQQQ","SQQQ","SOXL","SOXS"}:
        return "ETF"
    return "US"

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
    rank = providers.index(p)+1 if p in providers else 6
    score = max(55, 100-(rank-1)*10)
    if p.startswith("YAHOO"):
        score -= 8
    return max(0, min(100, score))

def thai_time():
    return (datetime.now(timezone.utc)+timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")

def session(mkt):
    h = (datetime.now(timezone.utc)+timedelta(hours=7)).hour
    if mkt in {"US","ETF"}:
        if 15 <= h < 20:
            return "PREMARKET", "ใช้ราคา Pre-market ถ้ามี"
        if 20 <= h or h < 4:
            return "US_SESSION", "ใช้ราคา Regular/Extended"
        return "CLOSED", "ตลาดปิด ใช้ราคาปิดล่าสุด + pre/after เป็นข้อมูลประกอบ"
    if mkt == "TH":
        return ("TH_OPEN", "หุ้นไทยระหว่างวัน/ดีเลย์") if 10 <= h < 17 else ("TH_CLOSED", "ตลาดไทยปิด ใช้ราคาปิดล่าสุด")
    if mkt == "GOLD":
        return "GOLD_LIVE", "ทองใช้ราคาสมาคมค้าทองคำเป็นหลัก"
    return "LATEST", "ข้อมูลล่าสุด"

def health(symbol=None):
    if symbol:
        s = normalize(symbol)
        m = market(s)
        lines = [f"🔎 สถานะข้อมูล {s}", f"ตลาด: {m}", f"แหล่งหลัก: {source(m)}", f"ความน่าเชื่อถือ: {reliability(m)}/100"]
        for p in PRIORITY.get(m, []):
            lines.append(("✅" if ready(p) else "❌") + f" {p}")
    else:
        lines = ["🧭 สถานะระบบ V1412.1"]
        for m in ["US","ETF","TH","GOLD","MACRO"]:
            lines.append(f"{m}: {source(m)} | {reliability(m)}/100")
    lines.append("")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)
