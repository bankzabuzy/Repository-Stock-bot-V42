"""
market_brain.py — V1416 LIVE DATA ENGINE
=========================================
แก้ไขจาก V1415: เปลี่ยนจาก hardcode FALLBACK → ดึงข้อมูล live จริง
โดยใช้ฟังก์ชันที่มีอยู่แล้วใน main.py ผ่าน sys.modules

หลักการ:
  1. พยายามดึงข้อมูลจริงจาก main.py (get_market_data + analyze_signal)
  2. ถ้าดึงไม่ได้ → ใช้ FALLBACK เป็น last resort (ไม่ crash)
  3. ทุก AssetSnapshot ที่ return จะมี is_live=True/False บอกสถานะ

ลำดับ data source (เรียงตามความเชื่อถือได้):
  Yahoo Finance (yfinance) → Yahoo Chart API → TwelveData → Finnhub → FALLBACK
"""

import os
import sys
import time
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────────────────────
# AssetSnapshot — เพิ่ม is_live + data_ts
# ─────────────────────────────────────────────────────────────
@dataclass
class AssetSnapshot:
    symbol: str
    name: str
    price: float
    prev_close: float
    premarket: object       # float | None
    regular: object         # float | None
    afterhours: object      # float | None
    score: int
    prob_up: int
    confidence: int
    risk_grade: str
    view: str
    ema6: float
    ema12: float
    ema50: float
    rsi14: float
    atr14: float
    rvol: float
    pe: object              # float | str
    forward_pe: object      # float | str
    dividend_yield: object  # float | str
    dividend_last: object   # float | str
    buy_ratio: int
    sell_ratio: int
    trend_15m: str
    trend_1h: str
    trend_4h: str
    trend_1d: str
    trend_1w: str
    key_reason: str
    news1: str
    news2: str
    # V1416 additions
    is_live: bool = False
    data_ts: str = ""
    source: str = "FALLBACK"
    change_pct: object = None   # float | None

# ─────────────────────────────────────────────────────────────
# FALLBACK — ใช้เฉพาะเมื่อ live data ไม่ได้จริงๆ
# ─────────────────────────────────────────────────────────────
FALLBACK = {
    "NVDA": AssetSnapshot("NVDA","NVIDIA",208.19,208.19,202.87,200.42,199.20,34,45,49,"C","BEARISH",211.41,213.67,206.96,40.11,8.57,1.01,30.69,15.75,0.50,0.25,46,54,"Bearish","Bearish","Neutral","Bullish","Bullish","แรงขายยังได้เปรียบ ราคาอยู่ใต้ EMA6/12","Bond yield และดอลลาร์กระทบหุ้นเทค","รอแรงซื้อกลับมาก่อนเข้า",False,"","FALLBACK",None),
    "QQQ":  AssetSnapshot("QQQ","Nasdaq 100 ETF",707.83,707.83,702.36,693.69,None,42,51,55,"B-","NEUTRAL",720.58,722.64,685.40,52.95,14.09,2.18,30.96,"N/A","N/A",0.73,48,52,"Mixed","Mixed","Neutral","Bullish","Bullish","โมเมนตัมยังไม่ชัด รอ breadth ยืนยัน","ตลาดเทคแกว่งตาม yield","รอทะลุแนวต้านก่อนเพิ่มไม้",False,"","FALLBACK",None),
    "SCB.BK":  AssetSnapshot("SCB.BK","SCB X",137.50,137.50,None,137.50,None,78,60,64,"B+","BULLISH",137.83,137.25,137.07,58.62,1.82,0.60,10.25,10.32,8.20,9.28,58,42,"N/A","N/A","N/A","Mixed","Mixed","ปันผลเด่น valuation ไม่แพง แต่ volume ยังไม่แรง","หุ้นธนาคารยังเด่นเชิงปันผล","ทยอยซื้อได้แต่ไม่ all in",False,"","FALLBACK",None),
    "KBANK.BK":AssetSnapshot("KBANK.BK","Kasikornbank",126.00,126.00,None,126.00,None,67,56,58,"B","WATCH",126.5,125.8,122.0,55.2,1.9,0.75,9.8,"N/A",5.0,"N/A",54,46,"N/A","N/A","N/A","Mixed","Mixed","กลุ่มธนาคารแข็งแต่ต้องรอ volume","Bank sector ยังมีแรงหนุน","รอจังหวะย่อ",False,"","FALLBACK",None),
    "BBL.BK":  AssetSnapshot("BBL.BK","Bangkok Bank",154.00,154.00,None,154.00,None,65,55,57,"B","WATCH",154.2,153.6,150.0,54.1,2.1,0.72,8.9,"N/A",4.8,"N/A",53,47,"N/A","N/A","N/A","Mixed","Mixed","หุ้น value ต้องรอ volume","Valuation ไม่แพง","รอทะลุแนวต้าน",False,"","FALLBACK",None),
    "PTT.BK":  AssetSnapshot("PTT.BK","PTT",34.00,34.00,None,34.00,None,61,53,55,"B-","WATCH",34.1,34.0,33.5,51.2,0.45,0.85,10.5,"N/A",5.3,"N/A",51,49,"N/A","N/A","N/A","Mixed","Mixed","ขึ้นกับราคาน้ำมันและตลาดรวม","Energy sector รอ catalyst","เข้าเล็กเมื่อยืนแนวรับ",False,"","FALLBACK",None),
    "AOT.BK":  AssetSnapshot("AOT.BK","Airports of Thailand",61.00,61.00,None,61.00,None,58,52,54,"C+","WATCH",61.4,61.0,60.0,50.8,0.9,0.70,35.0,"N/A",1.0,"N/A",50,50,"N/A","N/A","N/A","Mixed","Mixed","valuation สูง ต้องรอแรงซื้อชัด","ท่องเที่ยวฟื้นแต่ราคาไม่ถูก","รอย่อ",False,"","FALLBACK",None),
    "GOLD":    AssetSnapshot("GOLD","Thai Gold",63850,63850,None,63850,None,52,48,44,"C","WAIT",4118,4109,4050,56.2,32.4,1.0,"N/A","N/A","N/A","N/A",45,55,"Neutral","Neutral","Bearish","Bearish","Mixed","รอ London/NY และ DXY/Yield ยืนยัน","ทองไทยใช้ราคาสมาคมเป็นหลัก","ยังไม่ใช่จุดไล่ซื้อ",False,"","FALLBACK",None),
}

# ─────────────────────────────────────────────────────────────
# Live snapshot cache (TTL 3 นาที)
# ─────────────────────────────────────────────────────────────
_live_cache: dict = {}
_cache_lock = threading.Lock()
CACHE_TTL_SECS = 180

def _cache_get(sym: str):
    with _cache_lock:
        entry = _live_cache.get(sym)
        if entry and (time.time() - entry["ts"]) < CACHE_TTL_SECS:
            return entry["snap"]
    return None

def _cache_set(sym: str, snap: AssetSnapshot):
    with _cache_lock:
        _live_cache[sym] = {"snap": snap, "ts": time.time()}

# ─────────────────────────────────────────────────────────────
# Helpers — ดึง functions จาก main.py runtime
# ─────────────────────────────────────────────────────────────
def _main():
    """Return main module safely."""
    return sys.modules.get("__main__") or sys.modules.get("main")

def _fn(name):
    """Return function from main by name, or None."""
    m = _main()
    return getattr(m, name, None) if m else None

def _safe_float(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except Exception:
        return default

def _now_ts() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=7)).strftime("%d/%m %H:%M")

# ─────────────────────────────────────────────────────────────
# Risk grade from score
# ─────────────────────────────────────────────────────────────
def _risk_grade(score: int, signal: str = "", rsi: float = 50, rvol: float = 1.0) -> str:
    s = str(signal or "").upper()
    penalty = 0
    if rsi >= 76: penalty += 1
    if rvol >= 2.2: penalty += 1
    if s in {"SELL","STRONG_PUT","PUT"}: penalty += 2
    if score >= 85 and penalty == 0: return "A"
    if score >= 75 and penalty <= 1: return "B+"
    if score >= 62: return "B"
    if score >= 50: return "C+"
    if score >= 40: return "C"
    return "D"

# ─────────────────────────────────────────────────────────────
# MTF trend strings
# ─────────────────────────────────────────────────────────────
def _trend_str(ema_short, ema_long, price) -> str:
    try:
        if price > ema_short > ema_long: return "Bullish"
        if price < ema_short < ema_long: return "Bearish"
        return "Mixed"
    except Exception:
        return "N/A"

# ─────────────────────────────────────────────────────────────
# Pre/post market
# ─────────────────────────────────────────────────────────────
def _get_prepost(symbol: str, asset_type: str):
    """Try Yahoo preMarketPrice / postMarketPrice via yfinance."""
    pre = None
    post = None
    try:
        if asset_type not in ("US_STOCK", "ETF"):
            return pre, post
        import yfinance as yf
        t = yf.Ticker(symbol)
        info = {}
        try:
            info = t.get_info() or {}
        except Exception:
            try:
                info = t.info or {}
            except Exception:
                pass
        pre  = _safe_float(info.get("preMarketPrice"), None) if info.get("preMarketPrice") else None
        post = _safe_float(info.get("postMarketPrice"), None) if info.get("postMarketPrice") else None
    except Exception:
        pass
    return pre, post

# ─────────────────────────────────────────────────────────────
# News headlines (Finnhub → Yahoo RSS)
# ─────────────────────────────────────────────────────────────
def _get_news(symbol: str) -> tuple:
    """Return (news1, news2) string headlines."""
    n1, n2 = "", ""
    try:
        fetch_news = _fn("fetch_news")
        normalize_asset = _fn("normalize_asset")
        if fetch_news and normalize_asset:
            asset = normalize_asset(symbol)
            text, count = fetch_news(asset)
            if text and count > 0:
                lines = [l.strip() for l in text.strip().split("\n") if l.strip() and not l.startswith("📰")]
                headlines = [l for l in lines if len(l) > 10]
                n1 = headlines[0][:80] if len(headlines) > 0 else ""
                n2 = headlines[1][:80] if len(headlines) > 1 else ""
    except Exception:
        pass
    return n1, n2

# ─────────────────────────────────────────────────────────────
# LIVE SNAPSHOT — core function
# ─────────────────────────────────────────────────────────────
def _build_live_snapshot(symbol: str) -> AssetSnapshot | None:
    """
    ดึงข้อมูลจริงจาก main.py pipeline แล้ว map เข้า AssetSnapshot.
    Return None ถ้า error ทุก provider.
    """
    normalize_asset   = _fn("normalize_asset")
    get_market_data   = _fn("get_market_data")
    analyze_signal    = _fn("analyze_signal")
    signal_type_fn    = _fn("signal_type_from_analysis")
    resolve_delisted  = _fn("resolve_delisted_symbol")
    calc_confidence   = _fn("calculate_signal_confidence")

    if not all([normalize_asset, get_market_data, analyze_signal]):
        return None   # main.py not ready yet

    try:
        sym = resolve_delisted(symbol) if resolve_delisted else symbol
        asset = normalize_asset(sym)
        quote, closes, highs, lows, opens, volumes = get_market_data(asset)
        analysis = analyze_signal(asset, quote, closes, highs, lows, opens, volumes)

        price       = _safe_float(analysis.get("price"))
        prev        = _safe_float(analysis.get("previous_close"))
        score       = max(0, min(100, int(analysis.get("score") or 50)))
        prob        = max(0, min(95,  int(analysis.get("probability") or 50)))
        rsi14       = _safe_float(analysis.get("rsi"), 50.0)
        atr14       = _safe_float(analysis.get("atr"), 0.0)
        rvol        = _safe_float(analysis.get("rvol"), 1.0)
        ema6        = _safe_float(analysis.get("ema6"))
        ema12       = _safe_float(analysis.get("ema12"))
        ema50       = _safe_float(analysis.get("ema50"))
        regime      = str(analysis.get("regime") or "NEUTRAL")
        bias        = str(analysis.get("bias") or "NEUTRAL")
        reasons     = analysis.get("reasons") or []
        source      = str(quote.get("source") or "Yahoo") if isinstance(quote, dict) else "Yahoo"

        # Signal
        if signal_type_fn:
            signal = signal_type_fn(asset, analysis)
        else:
            signal = "BUY" if score >= 70 else ("SELL" if score <= 30 else "NEUTRAL")

        # Confidence
        if calc_confidence:
            confidence = int(max(40, min(95, calc_confidence(analysis))))
        else:
            confidence = int(max(40, min(95, abs(score - 50) * 1.8 + 45)))

        # Grade
        grade = _risk_grade(score, signal, rsi14, rvol)

        # View
        bias_u = bias.upper()
        if "BULLISH" in bias_u or score >= 70:   view = "BULLISH"
        elif "BEARISH" in bias_u or score <= 35: view = "BEARISH"
        else:                                     view = "NEUTRAL"

        # Change pct
        change_pct = None
        if price and prev and prev > 0:
            change_pct = round((price - prev) / prev * 100, 2)

        # Trend strings from MTF
        trend_1d = _trend_str(ema6, ema12, price)
        trend_1w = _trend_str(ema12, ema50, price) if ema50 else "N/A"

        # Pre/Post market
        pre_price, post_price = _get_prepost(asset["symbol"], asset.get("asset_type",""))

        # News
        n1, n2 = _get_news(asset["symbol"])

        # Key reason
        key_reason = reasons[0][:80] if reasons else "ข้อมูลจากระบบ live"

        return AssetSnapshot(
            symbol       = asset.get("symbol", sym).upper(),
            name         = asset.get("name") or asset.get("symbol", sym).upper(),
            price        = price,
            prev_close   = prev,
            premarket    = pre_price,
            regular      = price,
            afterhours   = post_price,
            score        = score,
            prob_up      = prob,
            confidence   = confidence,
            risk_grade   = grade,
            view         = view,
            ema6         = ema6 or 0.0,
            ema12        = ema12 or 0.0,
            ema50        = ema50 or 0.0,
            rsi14        = rsi14,
            atr14        = atr14,
            rvol         = rvol,
            pe           = "N/A",
            forward_pe   = "N/A",
            dividend_yield = "N/A",
            dividend_last  = "N/A",
            buy_ratio    = min(99, max(1, score)),
            sell_ratio   = min(99, max(1, 100 - score)),
            trend_15m    = "N/A",
            trend_1h     = "N/A",
            trend_4h     = "N/A",
            trend_1d     = trend_1d,
            trend_1w     = trend_1w,
            key_reason   = key_reason,
            news1        = n1,
            news2        = n2,
            is_live      = True,
            data_ts      = _now_ts(),
            source       = source,
            change_pct   = change_pct,
        )
    except Exception as e:
        print(f"[market_brain] live snapshot error {symbol}: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────
from v1413_worldclass_line_os.api.priority_router import normalize_symbol, market_of

def get_snapshot(symbol: str) -> AssetSnapshot:
    """
    Main entry point. ลำดับ:
    1. Live cache (TTL 3 นาที)
    2. Live data จาก main.py pipeline
    3. FALLBACK hardcode (last resort)
    """
    sym = normalize_symbol(symbol)

    # 1. Cache
    cached = _cache_get(sym)
    if cached:
        return cached

    # 2. Live data
    snap = _build_live_snapshot(sym)
    if snap and snap.price and snap.price > 0:
        _cache_set(sym, snap)
        return snap

    # 3. Fallback — known symbols
    if sym in FALLBACK:
        return FALLBACK[sym]

    # 4. Generic fallback สำหรับ symbol ที่ไม่รู้จัก
    m = market_of(sym)
    if m == "TH":
        base = asdict(FALLBACK["SCB.BK"])
        base.update(symbol=sym, name=sym, score=50, prob_up=50, confidence=45,
                    risk_grade="C", view="WATCH",
                    key_reason="ไม่มีข้อมูล live — ใช้ค่าอนุรักษ์นิยม",
                    is_live=False, source="FALLBACK", data_ts=_now_ts())
        return AssetSnapshot(**base)
    if m == "GOLD":
        return FALLBACK["GOLD"]
    base = asdict(FALLBACK["QQQ"])
    base.update(symbol=sym, name=sym, score=50, prob_up=50, confidence=45,
                risk_grade="C", view="NEUTRAL",
                key_reason="ไม่มีข้อมูล live — ใช้ค่าอนุรักษ์นิยม",
                is_live=False, source="FALLBACK", data_ts=_now_ts())
    return AssetSnapshot(**base)


# ─────────────────────────────────────────────────────────────
# Utility functions (ใช้งานเหมือนเดิม — backward compatible)
# ─────────────────────────────────────────────────────────────
def expected_move(s: AssetSnapshot):
    atr = s.atr14 or max(s.price * 0.02, 1)
    high_1d = s.price + atr * 0.55
    low_1d  = s.price - atr * 0.85
    high_3d = s.price + atr * 1.25
    low_3d  = s.price - atr * 1.55
    down_prob   = max(5, 100 - s.prob_up - 5)
    sideways    = max(0, 100 - s.prob_up - down_prob)
    return {
        "up_prob": s.prob_up, "down_prob": down_prob, "sideways_prob": sideways,
        "high_1d": high_1d, "low_1d": low_1d,
        "high_3d": high_3d, "low_3d": low_3d,
        "expected_pct": (atr / s.price * 100) if s.price else 0,
    }

def trade_plan(s: AssetSnapshot):
    if s.prob_up < 50:
        return {
            "no_trade": True,
            "reason": "Probability ต่ำกว่า 50% รอให้ราคาเลือกทางก่อน",
            "entries": [], "tp": [], "sl": s.price - s.atr14 * 1.5,
        }
    atr = s.atr14 or max(s.price * 0.01, 1)
    return {
        "no_trade": False,
        "entries": [
            (round(s.price - atr*0.30, 2), s.confidence, 40),
            (round(s.price - atr*0.70, 2), max(20, s.confidence-8), 30),
            (round(s.price - atr*1.10, 2), max(10, s.confidence-20), 30),
        ],
        "tp": [round(s.price + atr*0.45, 2), round(s.price + atr*0.95, 2), round(s.price + atr*1.55, 2)],
        "sl": round(s.price - atr*1.50, 2),
    }

def risk_sentence(s: AssetSnapshot) -> str:
    if s.risk_grade.startswith("A"):  return "🟢 เสี่ยงต่ำ/จังหวะดี"
    if s.risk_grade.startswith("B"):  return "🟡 เสี่ยงกลาง คุมไม้ได้"
    if s.risk_grade.startswith("C"):  return "🟠 เสี่ยงสูง ต้องรอจังหวะ"
    return "🔴 หลีกเลี่ยง"

def entry_score(s: AssetSnapshot) -> float:
    score = 5.0
    if s.prob_up >= 60: score += 1.2
    if s.rsi14 >= 50:   score += 0.6
    if s.rvol >= 1:     score += 0.5
    if s.price > s.ema50: score += 0.5
    if s.prob_up < 50:  score -= 1.0
    return max(1.0, min(10.0, round(score, 1)))


# V1418 compatibility: Thai Gold Association fallback values.
THAI_GOLD = {
    "bar_buy": 63650,
    "bar_sell": 63850,
    "orn_buy": 62383,
    "orn_sell": 64650,
    "spread": 200,
    "xauusd": 4115.60,
    "usdthb": 32.91,
}
