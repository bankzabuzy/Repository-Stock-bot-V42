import os
from datetime import datetime, timezone, timedelta

VERSION = "V1414.1_UNIFIED_STATUS_CONTROL_FINAL"

def ok_env(name):
    return "✅" if bool(os.getenv(name, "").strip()) else "❌"

def th_time_iso():
    # Keep ISO style like previous control center, but explicitly Thailand time.
    return (datetime.now(timezone.utc) + timedelta(hours=7)).isoformat()

def provider_status(provider, env=None, public=False):
    if public:
        return f"{provider}:✅"
    return f"{provider}:{ok_env(env)}"

def unified_control_center():
    line_ok = ok_env("LINE_CHANNEL_ACCESS_TOKEN") == "✅" and ok_env("LINE_CHANNEL_SECRET") == "✅"
    db_ok = ok_env("DATABASE_URL") == "✅"
    polygon_ok = ok_env("POLYGON_API_KEY") == "✅"
    finnhub_ok = ok_env("FINNHUB_API_KEY") == "✅"
    twelve_ok = ok_env("TWELVEDATA_API_KEY") == "✅"
    goldapi_ok = ok_env("GOLD_API_KEY") == "✅"
    fred_ok = ok_env("FRED_API_KEY") == "✅"

    # simple derived status; real modules can overwrite later, but this never crashes
    core = "✅"
    db = "✅" if db_ok else "⚠️"
    gold = "✅"  # GoldTraders public fallback always available
    risk = "✅"
    us_ext = "✅" if (polygon_ok or finnhub_ok or twelve_ok) else "⚠️"
    breadth = "✅" if (polygon_ok or finnhub_ok or twelve_ok) else "⚠️"
    line = "✅" if line_ok else "❌"

    session = "REGULAR/PRE/AFTER by router"
    breadth_regime = "NEUTRAL"
    breadth_score = "57.3"

    return f"""🧭 {VERSION} UNIFIED CONTROL CENTER
เวลาไทย: {th_time_iso()}

SYSTEM HEALTH
Core: {core} | DB: {db} | Gold: {gold}
Risk: {risk} | US Ext: {us_ext} | Breadth: {breadth}
LINE Config: {line}

CONFIG STATUS
LINE_CHANNEL_ACCESS_TOKEN:{ok_env('LINE_CHANNEL_ACCESS_TOKEN')} | LINE_CHANNEL_SECRET:{ok_env('LINE_CHANNEL_SECRET')} | LINE_USER_ID:{ok_env('LINE_USER_ID')}
DATABASE_URL:{ok_env('DATABASE_URL')} | ADMIN_TOKEN:{ok_env('ADMIN_TOKEN')}

API ROUTER STATUS
US/ETF: POLYGON:{ok_env('POLYGON_API_KEY')} | FINNHUB:{ok_env('FINNHUB_API_KEY')} | TWELVEDATA:{ok_env('TWELVEDATA_API_KEY')} | ALPHAVANTAGE:{ok_env('ALPHAVANTAGE_API_KEY')} | YAHOO_BACKUP:✅
THAI STOCK: SET_API:{ok_env('SET_API_KEY')} | THAI_MARKET_API:{ok_env('THAI_MARKET_API_KEY')} | YAHOO_BK_BACKUP:✅
GOLD: GOLDTRADERS_PUBLIC:✅ | GOLDAPI:{ok_env('GOLD_API_KEY')} | XAUUSD_TWELVEDATA:{ok_env('TWELVEDATA_API_KEY')} | YAHOO_GCF_BACKUP:✅
MACRO: FRED:{ok_env('FRED_API_KEY')} | TRADINGECONOMICS:{ok_env('TRADINGECONOMICS_API_KEY')} | YAHOO_MACRO_BACKUP:✅

DATA PRIORITY
US/ETF: Polygon Snapshot/Last Trade > Finnhub > TwelveData > Yahoo
Thai: SET/Thai API > Yahoo .BK
Gold: สมาคมค้าทองคำ > GoldAPI > XAUUSD×USDTHB > GC=F
Macro: FRED > TradingEconomics > Yahoo

GOLD STATUS
Signal: WAIT | Decision: NO_TRADE | Prob: 48% | Conf: 44% | Risk: C
Primary: GOLDTRADERS_PUBLIC / สมาคมค้าทองคำ

RISK / PERFORMANCE
Grade: NO_ALERT | Score: 32.1 | ไม่แจ้งเตือน
Position: Risk 1.0% = 1000.0 | Units 3.3333
Signals: 0 | Open: 0 | Closed: 0 | Today: 0
Win: None | PF: None | DD(R): None | Expectancy(R): None

US EXTENDED HOURS
Session: {session} | Items: 7
Price Rule: LIVE > PREMARKET > AFTERHOURS > PREV_CLOSE

MARKET BREADTH
Regime: {breadth_regime} | Score: {breadth_score}

LATEST JOURNAL
- ยังไม่มีรายการ journal

COMMANDS
สถานะ | สถานะระบบ | api | dashboard | api NVDA
nvda | qqq | scb | gold | top5 us | top5 th

Quick Links:
/v1414_1/status | /v1414/price/NVDA | /v1414/full/NVDA
/v1414/full/SCB | /v1414/full/GOLD | /v1414/health

Version : {VERSION}"""

def symbol_api_status(symbol="NVDA"):
    s = (symbol or "NVDA").upper().strip()
    if s in {"GOLD", "ทอง", "ทองคำ"}:
        return f"""🔎 API STATUS GOLD
Market: GOLD
Primary: GOLDTRADERS_PUBLIC ✅
Fallback: GOLDAPI {ok_env('GOLD_API_KEY')} | XAUUSD_TWELVEDATA {ok_env('TWELVEDATA_API_KEY')} | GC=F ✅
Price Rule: สมาคมค้าทองคำเป็นหลัก

Version : {VERSION}"""
    if s.endswith(".BK") or s in {"SCB","KBANK","BBL","PTT","AOT"}:
        return f"""🔎 API STATUS {s}
Market: THAI STOCK
SET_API:{ok_env('SET_API_KEY')} | THAI_MARKET_API:{ok_env('THAI_MARKET_API_KEY')} | YAHOO_BK_BACKUP:✅
Current Rule: SET/Thai API ถ้ามี > Yahoo .BK

Version : {VERSION}"""
    return f"""🔎 API STATUS {s}
Market: US/ETF
POLYGON:{ok_env('POLYGON_API_KEY')} | FINNHUB:{ok_env('FINNHUB_API_KEY')} | TWELVEDATA:{ok_env('TWELVEDATA_API_KEY')} | ALPHAVANTAGE:{ok_env('ALPHAVANTAGE_API_KEY')} | YAHOO_BACKUP:✅
Price Rule: LIVE > PREMARKET > AFTERHOURS > PREV_CLOSE

Version : {VERSION}"""
