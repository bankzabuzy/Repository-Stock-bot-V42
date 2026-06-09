# V42 GOLD INSTITUTIONAL
# Stable Thai Gold + XAUUSD decision-support engine.
# Designed to fail-safe: no exception should crash the Flask worker.

from __future__ import annotations

import os
import re
import math
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import requests

try:
    import yfinance as yf  # type: ignore
except Exception:  # pragma: no cover
    yf = None

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None

V42_GOLD_VERSION = "V42.2_GOLD_INSTITUTIONAL_ENTRY_FILTER_STABLE"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_FALLBACK_XAUUSD = float(os.getenv("FALLBACK_XAUUSD", "2350") or 2350)
_FALLBACK_USDTHB = float(os.getenv("FALLBACK_USDTHB", "36.50") or 36.50)
_CACHE: Dict[str, Any] = {}
_CACHE_TS: Dict[str, datetime] = {}


def now_th() -> str:
    return datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")


def _cache_get(key: str, ttl_sec: int = 180) -> Any:
    ts = _CACHE_TS.get(key)
    if ts and (datetime.now(timezone.utc) - ts).total_seconds() <= ttl_sec:
        return _CACHE.get(key)
    return None


def _cache_set(key: str, val: Any) -> Any:
    _CACHE[key] = val
    _CACHE_TS[key] = datetime.now(timezone.utc)
    return val


def safe_float(x: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if x is None:
            return default
        if isinstance(x, str):
            x = x.replace(",", "").replace("฿", "").replace("$", "").strip()
            if x in {"", "-", "N/A", "None"}:
                return default
        return float(x)
    except Exception:
        return default


def fmt_num(x: Any, digits: int = 2) -> str:
    v = safe_float(x)
    if v is None:
        return "N/A"
    if digits == 0:
        return f"{v:,.0f}"
    return f"{v:,.{digits}f}"


def _text_from_html(html: str) -> str:
    if BeautifulSoup is None:
        return re.sub(r"<[^>]+>", " ", html)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ", strip=True)


def _parse_goldtraders_text(text: str, source: str, raw_url: str) -> Optional[Dict[str, Any]]:
    # UpdatePriceList-like rows: date time round bar_buy bar_sell ornament_buy ornament_sell spot usdthb change
    row = re.search(
        r"(\d{2}/\d{2}/\d{4})\s+(\d{1,2}:\d{2})\s+(\d+)\s+"
        r"(\d{2,3},\d{3}(?:\.\d{2})?)\s+(\d{2,3},\d{3}(?:\.\d{2})?)\s+"
        r"(\d{2,3},\d{3}(?:\.\d{2})?)\s+(\d{2,3},\d{3}(?:\.\d{2})?)"
        r"(?:\s+(\d{1,2},\d{3}(?:\.\d{2})?))?(?:\s+(\d{2}(?:\.\d{2})?))?(?:\s+([+-]?\d+))?",
        text,
    )
    if row:
        return {
            "ok": True,
            "bar_buy": safe_float(row.group(4)),
            "bar_sell": safe_float(row.group(5)),
            "ornament_buy": safe_float(row.group(6)),
            "ornament_sell": safe_float(row.group(7)),
            "gold_spot": safe_float(row.group(8)),
            "usd_thb_ref": safe_float(row.group(9)),
            "change": safe_float(row.group(10), 0),
            "source": source,
            "updated_at": f"{row.group(1)} {row.group(2)} ครั้งที่ {row.group(3)}",
            "raw_url": raw_url,
            "is_estimate": False,
        }

    # Loose homepage Thai labels
    bar = re.search(
        r"ทองคำแท่ง\s*96\.5%.*?รับซื้อ\s*(\d{2,3},\d{3}(?:\.\d{2})?).*?ขายออก\s*(\d{2,3},\d{3}(?:\.\d{2})?)",
        text,
        re.S,
    )
    orn = re.search(
        r"ทองรูปพรรณ\s*96\.5%.*?(?:ฐานภาษี|รับซื้อ)\s*(\d{2,3},\d{3}(?:\.\d{2})?).*?ขายออก\s*(\d{2,3},\d{3}(?:\.\d{2})?)",
        text,
        re.S,
    )
    if bar:
        return {
            "ok": True,
            "bar_buy": safe_float(bar.group(1)),
            "bar_sell": safe_float(bar.group(2)),
            "ornament_buy": safe_float(orn.group(1)) if orn else None,
            "ornament_sell": safe_float(orn.group(2)) if orn else None,
            "gold_spot": None,
            "usd_thb_ref": None,
            "change": None,
            "source": source,
            "updated_at": now_th(),
            "raw_url": raw_url,
            "is_estimate": False,
        }
    return None


def fetch_goldtraders_price() -> Optional[Dict[str, Any]]:
    cached = _cache_get("goldtraders", ttl_sec=120)
    if cached:
        return cached
    urls = [
        "https://classic.goldtraders.or.th/UpdatePriceList.aspx",
        "https://classic.goldtraders.or.th/DailyPrices.aspx",
        "https://classic.goldtraders.or.th/",
        "https://www.goldtraders.or.th/",
        "https://newgta.goldtraders.or.th/homepage_pre",
    ]
    errors = []
    for url in urls:
        try:
            r = requests.get(url, headers=REQUEST_HEADERS, timeout=6)
            if r.status_code != 200 or not r.text:
                errors.append(f"{url} status={r.status_code}")
                continue
            parsed = _parse_goldtraders_text(_text_from_html(r.text), "สมาคมค้าทองคำ / GoldTraders", url)
            if parsed and parsed.get("bar_sell"):
                return _cache_set("goldtraders", parsed)
        except Exception as e:
            errors.append(f"{url} {e}")
    _CACHE["goldtraders_errors"] = errors[-5:]
    return None


def _yf_last_price(symbol: str, fallback: float) -> float:
    if yf is None:
        return fallback
    try:
        hist = yf.Ticker(symbol).history(period="5d", interval="1d")
        if hist is not None and not hist.empty:
            return float(hist["Close"].dropna().iloc[-1])
    except Exception:
        pass
    return fallback


def fetch_xauusd() -> Dict[str, Any]:
    cached = _cache_get("xauusd", ttl_sec=120)
    if cached:
        return cached
    price = _yf_last_price("GC=F", _FALLBACK_XAUUSD)
    if price == _FALLBACK_XAUUSD:
        price = _yf_last_price("XAUUSD=X", _FALLBACK_XAUUSD)
    usdthb = _yf_last_price("USDTHB=X", _FALLBACK_USDTHB)
    return _cache_set("xauusd", {"xauusd": price, "usd_thb": usdthb, "source": "Yahoo Finance GC=F / USDTHB=X"})


def gold_thb_per_baht_weight(xauusd: Optional[float], usdthb: Optional[float]) -> Optional[float]:
    if not xauusd or not usdthb:
        return None
    return float(xauusd) * float(usdthb) * (15.244 / 31.1034768)


def _parse_loose_gold_price_from_text(text: str, source: str, raw_url: str) -> Optional[Dict[str, Any]]:
    """Best-effort parser for public Thai gold price pages.
    It is intentionally conservative: only returns when at least 2 baht-weight prices are found.
    """
    nums = [safe_float(x) for x in re.findall(r"\b(\d{2,3},\d{3}(?:\.\d{2})?)\b", text or "")]
    nums = [float(x) for x in nums if x and 30000 <= float(x) <= 120000]
    uniq = []
    for n in nums:
        if n not in uniq:
            uniq.append(n)
    if len(uniq) < 2:
        return None
    uniq = sorted(uniq)
    bar_buy = uniq[0]
    bar_sell = uniq[1] if len(uniq) > 1 else uniq[0] + 100
    ornament_buy = uniq[2] if len(uniq) > 2 else max(bar_buy - 800, 0)
    ornament_sell = uniq[-1] if len(uniq) > 3 else bar_sell + 850
    return {
        "ok": True,
        "bar_buy": bar_buy,
        "bar_sell": bar_sell,
        "ornament_buy": ornament_buy,
        "ornament_sell": ornament_sell,
        "gold_spot": None,
        "usd_thb_ref": None,
        "change": None,
        "source": source,
        "updated_at": now_th(),
        "raw_url": raw_url,
        "is_estimate": False,
    }


def fetch_huasengheng_price() -> Optional[Dict[str, Any]]:
    cached = _cache_get("huasengheng", ttl_sec=120)
    if cached:
        return cached
    urls = [
        "https://www.huasengheng.com/",
        "https://www.huasengheng.com/gold-price/",
    ]
    errors = []
    for url in urls:
        try:
            r = requests.get(url, headers=REQUEST_HEADERS, timeout=5)
            if r.status_code != 200 or not r.text:
                errors.append(f"{url} status={r.status_code}")
                continue
            parsed = _parse_loose_gold_price_from_text(_text_from_html(r.text), "ฮั่วเซ่งเฮง / Huasengheng", url)
            if parsed and parsed.get("bar_sell"):
                parsed["fallback_level"] = 2
                return _cache_set("huasengheng", parsed)
        except Exception as e:
            errors.append(f"{url} {e}")
    _CACHE["huasengheng_errors"] = errors[-5:]
    return None


def fetch_ylg_price() -> Optional[Dict[str, Any]]:
    cached = _cache_get("ylg", ttl_sec=120)
    if cached:
        return cached
    urls = [
        "https://www.ylgbullion.co.th/",
        "https://www.ylgbullion.co.th/gold-price",
    ]
    errors = []
    for url in urls:
        try:
            r = requests.get(url, headers=REQUEST_HEADERS, timeout=5)
            if r.status_code != 200 or not r.text:
                errors.append(f"{url} status={r.status_code}")
                continue
            parsed = _parse_loose_gold_price_from_text(_text_from_html(r.text), "YLG Bullion", url)
            if parsed and parsed.get("bar_sell"):
                parsed["fallback_level"] = 3
                return _cache_set("ylg", parsed)
        except Exception as e:
            errors.append(f"{url} {e}")
    _CACHE["ylg_errors"] = errors[-5:]
    return None


def get_thai_gold_v42() -> Dict[str, Any]:
    # 1) Gold Traders Association
    real = fetch_goldtraders_price()
    if real and real.get("bar_sell"):
        real["fallback_level"] = 1
        return real

    # 2) Huasengheng
    hsh = fetch_huasengheng_price()
    if hsh and hsh.get("bar_sell"):
        return hsh

    # 3) YLG
    ylg = fetch_ylg_price()
    if ylg and ylg.get("bar_sell"):
        return ylg

    # 4) XAUUSD × USDTHB estimate, never crash / never 404
    fx = fetch_xauusd()
    est_sell = gold_thb_per_baht_weight(fx.get("xauusd"), fx.get("usd_thb"))
    if est_sell:
        return {
            "ok": True,
            "bar_buy": est_sell - 100,
            "bar_sell": est_sell,
            "ornament_buy": est_sell - 800,
            "ornament_sell": est_sell + 850,
            "gold_spot": fx.get("xauusd"),
            "usd_thb_ref": fx.get("usd_thb"),
            "change": None,
            "source": "ประมาณจาก XAUUSD × USD/THB (ใช้เมื่อแหล่งราคาทองไทยล่ม)",
            "updated_at": now_th(),
            "raw_url": None,
            "is_estimate": True,
            "fallback_level": 4,
            "errors": {
                "goldtraders": _CACHE.get("goldtraders_errors", []),
                "huasengheng": _CACHE.get("huasengheng_errors", []),
                "ylg": _CACHE.get("ylg_errors", []),
            },
        }
    return {
        "ok": False,
        "source": "No gold source available",
        "updated_at": now_th(),
        "errors": {
            "goldtraders": _CACHE.get("goldtraders_errors", []),
            "huasengheng": _CACHE.get("huasengheng_errors", []),
            "ylg": _CACHE.get("ylg_errors", []),
        },
    }


def _series(symbol: str, period: str, interval: str) -> List[float]:
    if yf is None:
        return []
    try:
        h = yf.Ticker(symbol).history(period=period, interval=interval)
        if h is not None and not h.empty:
            return [float(x) for x in h["Close"].dropna().tolist()]
    except Exception:
        return []
    return []


def _ema(vals: List[float], n: int) -> Optional[float]:
    if not vals:
        return None
    k = 2 / (n + 1)
    ema = vals[0]
    for v in vals[1:]:
        ema = v * k + ema * (1 - k)
    return ema


def _rsi(vals: List[float], n: int = 14) -> Optional[float]:
    if len(vals) <= n:
        return None
    gains, losses = [], []
    for a, b in zip(vals[-n-1:-1], vals[-n:]):
        d = b - a
        gains.append(max(d, 0))
        losses.append(abs(min(d, 0)))
    avg_gain = sum(gains) / n
    avg_loss = sum(losses) / n
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _tf_status(vals: List[float]) -> Dict[str, Any]:
    if len(vals) < 20:
        return {"trend": "UNKNOWN", "score": 50, "rsi": None, "ema6": None, "ema12": None, "ema50": None}
    price = vals[-1]
    e6, e12, e50 = _ema(vals, 6), _ema(vals, 12), _ema(vals, 50)
    r = _rsi(vals)
    score = 50
    trend = "NEUTRAL"
    if e6 and e12 and price > e6 > e12:
        score += 15
        trend = "BULLISH"
    if e12 and e50 and e12 > e50:
        score += 15
    if r is not None:
        if 55 <= r <= 72:
            score += 15
        elif r > 78:
            score -= 10
        elif r < 40:
            score -= 10
    if e6 and e12 and price < e6 < e12:
        score -= 20
        trend = "BEARISH"
    return {"trend": trend, "score": max(0, min(100, score)), "rsi": r, "ema6": e6, "ema12": e12, "ema50": e50}


def xauusd_engine() -> Dict[str, Any]:
    tf_map = {
        "M15": ("GC=F", "5d", "15m"),
        "H1": ("GC=F", "1mo", "1h"),
        "H4": ("GC=F", "3mo", "1d"),
        "D1": ("GC=F", "6mo", "1d"),
    }
    tfs = {}
    for name, args in tf_map.items():
        vals = _series(*args)
        if not vals and args[0] == "GC=F":
            vals = _series("XAUUSD=X", args[1], args[2])
        tfs[name] = _tf_status(vals)

    scores = [v["score"] for v in tfs.values() if v.get("score") is not None]
    base = sum(scores) / len(scores) if scores else 50
    bullish = sum(1 for v in tfs.values() if v.get("trend") == "BULLISH")
    bearish = sum(1 for v in tfs.values() if v.get("trend") == "BEARISH")
    if bullish >= 3:
        signal = "STRONG_BUY" if base >= 78 else "BUY"
        regime = "STRONG UPTREND" if bullish >= 3 else "UPTREND"
    elif bearish >= 3:
        signal = "SELL"
        regime = "DOWNTREND"
    else:
        signal = "WAIT"
        regime = "MIXED"
    prob = max(35, min(92, int(base + (bullish - bearish) * 3)))
    risk = "A" if prob >= 85 and signal in {"BUY", "STRONG_BUY"} else "B+" if prob >= 75 else "B" if prob >= 60 else "C"
    return {"signal": signal, "regime": regime, "probability": prob, "risk_grade": risk, "timeframes": tfs, "score": round(base, 2)}


def news_ai() -> Dict[str, Any]:
    key = os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_TOKEN")
    if not key:
        return {"sentiment": "NEUTRAL", "headlines": [], "source": "No Finnhub key"}
    try:
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=5)
        r = requests.get(
            "https://finnhub.io/api/v1/company-news",
            params={"symbol": "GLD", "from": start.isoformat(), "to": today.isoformat(), "token": key},
            timeout=8,
        )
        rows = r.json() if r.status_code == 200 else []
        headlines = [str(x.get("headline", ""))[:120] for x in rows[:3] if isinstance(x, dict)]
        txt = " ".join(headlines).lower()
        bull_words = ["surge", "rise", "higher", "safe haven", "fed cut", "inflation", "war"]
        bear_words = ["fall", "drop", "lower", "fed hike", "strong dollar"]
        score = sum(w in txt for w in bull_words) - sum(w in txt for w in bear_words)
        sent = "BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL"
        return {"sentiment": sent, "headlines": headlines, "source": "Finnhub GLD news"}
    except Exception as e:
        return {"sentiment": "NEUTRAL", "headlines": [], "source": f"Finnhub error: {e}"}


def gold_trade_plan(bar_sell: Optional[float], prob: int, signal: str) -> Dict[str, Any]:
    if not bar_sell:
        return {}
    step = 150 if prob >= 80 else 200
    if signal in {"BUY", "STRONG_BUY"}:
        entries = [bar_sell - step, bar_sell - step * 2, bar_sell - step * 3]
        tps = [bar_sell + step, bar_sell + step * 2, bar_sell + step * 3]
        sl = bar_sell - step * 4
    elif signal == "SELL":
        entries = [bar_sell + step, bar_sell + step * 2, bar_sell + step * 3]
        tps = [bar_sell - step, bar_sell - step * 2, bar_sell - step * 3]
        sl = bar_sell + step * 4
    else:
        entries = [bar_sell - 150, bar_sell - 300, bar_sell - 450]
        tps = [bar_sell + 150, bar_sell + 300, bar_sell + 450]
        sl = bar_sell - 600
    return {"entries": entries, "take_profits": tps, "stop_loss": sl}


def should_push_alert(engine: Dict[str, Any]) -> bool:
    return engine.get("signal") in {"BUY", "STRONG_BUY", "SELL"} and int(engine.get("probability") or 0) >= 85 and engine.get("risk_grade") in {"A", "B+"}


def build_v42_gold_payload() -> Dict[str, Any]:
    thai = get_thai_gold_v42()
    fx = fetch_xauusd()
    engine = xauusd_engine()
    news = news_ai()
    # News adjustment, conservative only.
    if news.get("sentiment") == "BULLISH" and engine["signal"] in {"BUY", "STRONG_BUY", "WAIT"}:
        engine["probability"] = min(92, engine["probability"] + 3)
    elif news.get("sentiment") == "BEARISH" and engine["signal"] in {"BUY", "STRONG_BUY"}:
        engine["probability"] = max(40, engine["probability"] - 5)
        if engine["probability"] < 80:
            engine["signal"] = "WAIT"
    plan = gold_trade_plan(safe_float(thai.get("bar_sell")), int(engine.get("probability") or 50), engine.get("signal", "WAIT"))
    return {
        "ok": bool(thai.get("ok")),
        "version": V42_GOLD_VERSION,
        "time_th": now_th(),
        "thai_gold": thai,
        "xauusd": fx,
        "engine": engine,
        "news": news,
        "trade_plan": plan,
        "push_alert": should_push_alert(engine),
        "quality_rule": "แจ้งเตือนเฉพาะ Signal BUY/STRONG_BUY/SELL + Probability >=85 + Risk A/B+",
    }


def build_v42_gold_text() -> str:
    p = build_v42_gold_payload()
    tg = p.get("thai_gold", {})
    fx = p.get("xauusd", {})
    eng = p.get("engine", {})
    news = p.get("news", {})
    plan = p.get("trade_plan", {})
    entries = plan.get("entries", [])
    tps = plan.get("take_profits", [])
    tf = eng.get("timeframes", {})
    tf_line = " | ".join(f"{k}:{v.get('trend','UNKNOWN')}" for k, v in tf.items())
    note = "ราคาเป็นค่าประมาณจาก XAUUSD/USDT หากดึงสมาคมค้าทองคำไม่ได้" if tg.get("is_estimate") else "ใช้ราคาจากสมาคมค้าทองคำ"
    action = "น่าเข้า" if eng.get("signal") in {"BUY", "STRONG_BUY"} and eng.get("probability", 0) >= 80 else "ขาย/ลดความเสี่ยง" if eng.get("signal") == "SELL" else "รอจังหวะ"
    lines = [
        f"🏆 V42 GOLD INSTITUTIONAL",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        f"ราคาทองไทย: {note}",
        f"ทองแท่งรับซื้อ: {fmt_num(tg.get('bar_buy'), 0)} บาท",
        f"ทองแท่งขายออก: {fmt_num(tg.get('bar_sell'), 0)} บาท",
        f"ทองรูปพรรณรับซื้อ: {fmt_num(tg.get('ornament_buy'), 0)} บาท",
        f"ทองรูปพรรณขายออก: {fmt_num(tg.get('ornament_sell'), 0)} บาท",
        f"แหล่งข้อมูล: {tg.get('source', 'N/A')}",
        f"อัปเดต: {tg.get('updated_at', 'N/A')}",
        "",
        f"XAUUSD/GC=F: ${fmt_num(fx.get('xauusd'), 2)} | USDTHB: {fmt_num(fx.get('usd_thb'), 2)}",
        f"Signal: {eng.get('signal')} | Action: {action}",
        f"Probability: {eng.get('probability')}% | Risk: {eng.get('risk_grade')} | Regime: {eng.get('regime')}",
        f"Multi TF: {tf_line}",
        f"News AI: {news.get('sentiment')} ({news.get('source')})",
        "",
        "🧩 แผนเข้า/ออกทองไทย",
    ]
    if entries and tps:
        lines += [
            f"ซื้อ/เข้าไม้ 1: {fmt_num(entries[0], 0)} บาท",
            f"ซื้อ/เข้าไม้ 2: {fmt_num(entries[1], 0)} บาท",
            f"ซื้อ/เข้าไม้ 3: {fmt_num(entries[2], 0)} บาท",
            f"TP1: {fmt_num(tps[0], 0)} บาท",
            f"TP2: {fmt_num(tps[1], 0)} บาท",
            f"TP3: {fmt_num(tps[2], 0)} บาท",
            f"Stop Loss: {fmt_num(plan.get('stop_loss'), 0)} บาท",
        ]
    else:
        lines.append("ยังไม่พอข้อมูลสำหรับแผน TP/SL")
    lines += [
        "",
        "🚨 Auto LINE Push:",
        "พร้อมแจ้งเตือนทันที" if p.get("push_alert") else "ยังไม่แจ้งเตือน เพราะสัญญาณยังไม่เข้มข้นพอ",
        p.get("quality_rule", ""),
        "",
        f"Version : {V42_GOLD_VERSION}",
    ]
    return "\n".join(lines)



# ============================================================
# V42.3 GOLD INSTITUTIONAL HIGH CONVICTION STABLE
# High-conviction alert layer: Entry Score + Session + News + Spread
# + Smart Trailing Stop + STRONG BUY. Existing Thai Gold fallback remains intact.
# ============================================================
V42_GOLD_VERSION = "V42.3_GOLD_INSTITUTIONAL_HIGH_CONVICTION_STABLE"


def _env_bool(name: str, default: bool = False) -> bool:
    return str(os.getenv(name, "true" if default else "false")).strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def session_filter(now_utc: Optional[datetime] = None) -> Dict[str, Any]:
    """Allow higher-conviction alerts mainly during London/New York sessions.
    London: 07:00-16:59 UTC, New York: 12:00-21:59 UTC.
    Can be bypassed with V42_ALLOW_ALL_SESSIONS=true.
    """
    now_utc = now_utc or datetime.now(timezone.utc)
    hour = int(now_utc.hour)
    london = 7 <= hour <= 16
    new_york = 12 <= hour <= 21
    allowed_all = _env_bool("V42_ALLOW_ALL_SESSIONS", False)
    allowed = bool(allowed_all or london or new_york)
    if london and new_york:
        name = "LONDON_NEWYORK_OVERLAP"
    elif london:
        name = "LONDON"
    elif new_york:
        name = "NEW_YORK"
    else:
        name = "ASIA_OR_OFF_SESSION"
    return {"allowed": allowed, "session": name, "utc_hour": hour, "allow_all_sessions": allowed_all}


def high_impact_news_filter() -> Dict[str, Any]:
    """Fail-safe high-impact news filter.
    Set HIGH_IMPACT_NEWS_ACTIVE=true in Railway manually when FOMC/CPI/NFP/Powell is within 30 minutes.
    Optional HIGH_IMPACT_NEWS_EVENT can describe the event.
    """
    active = _env_bool("HIGH_IMPACT_NEWS_ACTIVE", False)
    event = os.getenv("HIGH_IMPACT_NEWS_EVENT", "FOMC/CPI/NFP/Powell")
    minutes = int(_env_float("HIGH_IMPACT_NEWS_WINDOW_MIN", 30))
    return {
        "blocked": active,
        "event": event if active else None,
        "window_minutes": minutes,
        "decision": "WAIT_NEWS" if active else "PASS",
    }


def spread_filter(thai_gold: Dict[str, Any], fx: Dict[str, Any]) -> Dict[str, Any]:
    """Reject alerts when spread is abnormal. Thai baht-gold spread is used when available.
    Defaults are conservative and adjustable in Railway variables:
    GOLD_MAX_THAI_SPREAD=450, GOLD_MAX_XAU_SPREAD=5.
    """
    bar_buy = safe_float(thai_gold.get("bar_buy"))
    bar_sell = safe_float(thai_gold.get("bar_sell"))
    thai_spread = None
    if bar_buy is not None and bar_sell is not None:
        thai_spread = abs(bar_sell - bar_buy)
    max_thai = _env_float("GOLD_MAX_THAI_SPREAD", 450)
    ok_thai = True if thai_spread is None else thai_spread <= max_thai
    # yfinance usually has no live bid/ask; allow manual override if available.
    xau_spread = safe_float(os.getenv("GOLD_CURRENT_XAU_SPREAD"), 0)
    max_xau = _env_float("GOLD_MAX_XAU_SPREAD", 5)
    ok_xau = xau_spread <= max_xau
    ok = bool(ok_thai and ok_xau)
    return {
        "ok": ok,
        "thai_spread": thai_spread,
        "max_thai_spread": max_thai,
        "xau_spread": xau_spread,
        "max_xau_spread": max_xau,
        "decision": "PASS" if ok else "NO_TRADE_SPREAD",
    }


def _market_snapshot(symbol: str = "GC=F", period: str = "1mo", interval: str = "1h") -> Dict[str, Any]:
    if yf is None:
        return {"closes": [], "volumes": [], "source": "yfinance unavailable"}
    try:
        h = yf.Ticker(symbol).history(period=period, interval=interval)
        if h is not None and not h.empty:
            closes = [float(x) for x in h["Close"].dropna().tolist()]
            volumes = [float(x) for x in h["Volume"].fillna(0).tolist()] if "Volume" in h.columns else []
            return {"closes": closes, "volumes": volumes, "source": symbol}
    except Exception:
        pass
    if symbol == "GC=F":
        return _market_snapshot("XAUUSD=X", period, interval)
    return {"closes": [], "volumes": [], "source": symbol}


def _volume_confirm(volumes: List[float]) -> bool:
    vols = [float(v) for v in (volumes or []) if v is not None and float(v) >= 0]
    if len(vols) < 21:
        return False
    avg20 = sum(vols[-21:-1]) / 20 if sum(vols[-21:-1]) > 0 else 0
    if avg20 <= 0:
        return False
    return vols[-1] >= avg20 * 1.05


def xauusd_engine() -> Dict[str, Any]:
    tf_specs = {
        "M15": ("5d", "15m"),
        "H1": ("1mo", "1h"),
        "H4": ("3mo", "1d"),
        "D1": ("6mo", "1d"),
    }
    tfs: Dict[str, Any] = {}
    volume_flags: List[bool] = []
    for name, (period, interval) in tf_specs.items():
        snap = _market_snapshot("GC=F", period, interval)
        status = _tf_status(snap.get("closes", []))
        status["volume_confirm"] = _volume_confirm(snap.get("volumes", []))
        status["source"] = snap.get("source")
        tfs[name] = status
        volume_flags.append(bool(status["volume_confirm"]))

    trends = [v.get("trend") for v in tfs.values()]
    bullish_count = sum(1 for x in trends if x == "BULLISH")
    bearish_count = sum(1 for x in trends if x == "BEARISH")
    scores = [float(v.get("score") or 50) for v in tfs.values()]
    base = sum(scores) / len(scores) if scores else 50.0

    h1 = tfs.get("H1", {}).get("trend")
    h4 = tfs.get("H4", {}).get("trend")
    d1 = tfs.get("D1", {}).get("trend")
    multi_tf_buy = bullish_count >= 3 and h1 == "BULLISH" and h4 == "BULLISH"
    multi_tf_sell = bearish_count >= 3 and h1 == "BEARISH" and h4 == "BEARISH"
    volume_confirm = any(volume_flags)

    if multi_tf_buy and base >= 78:
        signal = "STRONG_BUY"
        regime = "STRONG UPTREND"
    elif multi_tf_buy:
        signal = "BUY"
        regime = "UPTREND"
    elif multi_tf_sell:
        signal = "SELL"
        regime = "DOWNTREND"
    else:
        signal = "WAIT"
        regime = "MIXED"

    directional_boost = 4 if multi_tf_buy or multi_tf_sell else 0
    vol_boost = 3 if volume_confirm else -4
    probability = int(max(35, min(94, round(base + directional_boost + vol_boost))))
    confidence = int(max(35, min(94, probability + (3 if (h1 == h4 and h1 in {"BULLISH", "BEARISH"}) else -4))))
    risk_grade = "A" if probability >= 86 and confidence >= 88 and volume_confirm else "B+" if probability >= 80 else "B" if probability >= 65 else "C"

    return {
        "signal": signal,
        "regime": regime,
        "probability": probability,
        "confidence": confidence,
        "risk_grade": risk_grade,
        "timeframes": tfs,
        "score": round(base, 2),
        "multi_tf_aligned": bool(multi_tf_buy or multi_tf_sell),
        "volume_confirm": bool(volume_confirm),
        "direction": "BUY" if multi_tf_buy else "SELL" if multi_tf_sell else "WAIT",
        "trend_score": int(max(0, min(100, base + (bullish_count - bearish_count) * 5))),
    }


def gold_trade_plan(bar_sell: Optional[float], prob: int, signal: str) -> Dict[str, Any]:
    if not bar_sell:
        return {}
    entry_gap = 100 if prob >= 85 else 150
    risk_amt = 250 if prob >= 85 else 300
    reward1 = risk_amt * 2.1
    reward2 = risk_amt * 2.8
    reward3 = risk_amt * 3.5
    if signal in {"BUY", "STRONG_BUY"}:
        entries = [bar_sell - entry_gap, bar_sell - entry_gap * 2, bar_sell - entry_gap * 3]
        base_entry = entries[0]
        sl = base_entry - risk_amt
        tps = [base_entry + reward1, base_entry + reward2, base_entry + reward3]
    elif signal == "SELL":
        entries = [bar_sell + entry_gap, bar_sell + entry_gap * 2, bar_sell + entry_gap * 3]
        base_entry = entries[0]
        sl = base_entry + risk_amt
        tps = [base_entry - reward1, base_entry - reward2, base_entry - reward3]
    else:
        entries = [bar_sell - 150, bar_sell - 300, bar_sell - 450]
        base_entry = entries[0]
        sl = base_entry - 300
        tps = [base_entry + 450, base_entry + 650, base_entry + 850]
    rr = abs(tps[0] - base_entry) / max(abs(base_entry - sl), 1)
    return {"entries": entries, "take_profits": tps, "stop_loss": sl, "rr": round(rr, 2), "base_entry": base_entry}


def _score_rr(rr: float) -> float:
    return max(0, min(100, (float(rr or 0) / 2.5) * 100))


def _score_news(sentiment: str) -> float:
    s = str(sentiment or "NEUTRAL").upper()
    if s == "BULLISH":
        return 100
    if s == "NEUTRAL":
        return 70
    if s == "BEARISH":
        return 20
    return 60


def calculate_entry_score(probability: int, confidence: int, rr: float, trend_score: float, news_sentiment: str) -> Dict[str, Any]:
    rr_score = _score_rr(rr)
    news_score = _score_news(news_sentiment)
    score = (
        float(probability or 0) * 0.30 +
        float(confidence or 0) * 0.25 +
        rr_score * 0.20 +
        float(trend_score or 0) * 0.15 +
        news_score * 0.10
    )
    score = round(max(0, min(100, score)), 2)
    if score >= 90:
        grade = "A+"
    elif score >= 85:
        grade = "A"
    elif score >= 80:
        grade = "B+"
    else:
        grade = "NO_ALERT"
    return {
        "entry_score": score,
        "entry_grade": grade,
        "rr_score": round(rr_score, 2),
        "trend_score": round(float(trend_score or 0), 2),
        "news_score": news_score,
        "formula": "probability*0.30 + confidence*0.25 + rr_score*0.20 + trend_score*0.15 + news_score*0.10",
    }


def smart_trailing_stop(plan: Dict[str, Any], current_price: Optional[float] = None, direction: str = "BUY") -> Dict[str, Any]:
    entries = plan.get("entries") or []
    tps = plan.get("take_profits") or []
    sl = plan.get("stop_loss")
    if not entries or len(tps) < 3 or sl is None:
        return {"enabled": False, "reason": "missing_plan"}
    entry = float(plan.get("base_entry") or entries[0])
    price = safe_float(current_price, entry)
    direction = str(direction or "BUY").upper()
    new_sl = sl
    stage = "PRE_TP1"
    if direction == "SELL":
        if price <= tps[0]:
            new_sl = entry
            stage = "TP1_MOVE_SL_TO_BE"
        if price <= tps[1]:
            new_sl = tps[0]
            stage = "TP2_LOCK_PROFIT"
        if price <= tps[2]:
            stage = "TP3_CLOSE_ALL"
    else:
        if price >= tps[0]:
            new_sl = entry
            stage = "TP1_MOVE_SL_TO_BE"
        if price >= tps[1]:
            new_sl = tps[0]
            stage = "TP2_LOCK_PROFIT"
        if price >= tps[2]:
            stage = "TP3_CLOSE_ALL"
    return {"enabled": True, "stage": stage, "entry": entry, "original_sl": sl, "new_sl": new_sl, "rule": "TP1→BE, TP2→lock profit, TP3→close all"}


def strong_buy_engine(engine: Dict[str, Any], news: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
    probability = int(engine.get("probability") or 0)
    confidence = int(engine.get("confidence") or 0)
    risk = str(engine.get("risk_grade") or "C")
    rr = float(plan.get("rr") or 0)
    mtf = bool(engine.get("multi_tf_aligned"))
    news_positive = str(news.get("sentiment") or "NEUTRAL").upper() == "BULLISH"
    passed = (
        probability >= 90 and
        confidence >= 90 and
        risk == "A" and
        rr >= 2.5 and
        mtf and
        news_positive
    )
    return {
        "passed": passed,
        "label": "STRONG_BUY" if passed else "NOT_STRONG_BUY",
        "checks": {
            "probability_ge_90": probability >= 90,
            "confidence_ge_90": confidence >= 90,
            "risk_A": risk == "A",
            "rr_ge_2_5": rr >= 2.5,
            "multi_tf_aligned": mtf,
            "news_positive": news_positive,
        },
    }


def institutional_entry_filter(engine: Dict[str, Any], news: Dict[str, Any], plan: Dict[str, Any], session: Dict[str, Any], news_event: Dict[str, Any], spread: Dict[str, Any], entry_score: Dict[str, Any], strong_buy: Dict[str, Any]) -> Dict[str, Any]:
    signal = str(engine.get("signal") or "WAIT")
    probability = int(engine.get("probability") or 0)
    confidence = int(engine.get("confidence") or 0)
    risk_grade = str(engine.get("risk_grade") or "C")
    news_sentiment = str(news.get("sentiment") or "NEUTRAL")
    rr = float(plan.get("rr") or 0)

    checks = {
        "signal_quality": signal in {"BUY", "STRONG_BUY", "SELL"},
        "multi_tf_aligned": bool(engine.get("multi_tf_aligned")),
        "volume_confirm": bool(engine.get("volume_confirm")),
        "probability_gt_80": probability > 80,
        "confidence_gt_85": confidence > 85,
        "news_not_negative": news_sentiment != "BEARISH",
        "rr_gt_2": rr > 2.0,
        "risk_grade_ok": risk_grade in {"A", "B+"},
        "session_ok": bool(session.get("allowed")),
        "high_impact_news_ok": not bool(news_event.get("blocked")),
        "spread_ok": bool(spread.get("ok")),
        "entry_score_ok": entry_score.get("entry_grade") in {"A+", "A", "B+"},
    }
    passed = all(checks.values())
    failed = [k for k, v in checks.items() if not v]
    if news_event.get("blocked"):
        decision = "WAIT_NEWS"
        action = "รอข่าวแรงผ่านก่อน"
    elif not session.get("allowed"):
        decision = "WAIT_SESSION"
        action = "รอ London/New York Session"
    elif not spread.get("ok"):
        decision = "NO_TRADE_SPREAD"
        action = "Spread สูงผิดปกติ"
    elif strong_buy.get("passed"):
        decision = "HIGH_CONVICTION_PUSH"
        action = "STRONG BUY ผ่านทุกเงื่อนไข Institutional"
    elif passed:
        decision = "PUSH_ALERT"
        action = "เข้าเงื่อนไขแจ้งเตือนทันที"
    elif signal in {"BUY", "STRONG_BUY", "SELL"} and probability > 75:
        decision = "WATCH_ONLY"
        action = "เฝ้าดู รอเงื่อนไขครบ"
    else:
        decision = "NO_TRADE"
        action = "ยังไม่เข้าเงื่อนไข"
    return {"passed": passed or bool(strong_buy.get("passed")), "decision": decision, "action": action, "checks": checks, "failed_checks": failed}


def should_push_alert(engine: Dict[str, Any], news: Optional[Dict[str, Any]] = None, plan: Optional[Dict[str, Any]] = None) -> bool:
    session = session_filter()
    news_event = high_impact_news_filter()
    spread = {"ok": True}
    entry_score = calculate_entry_score(int(engine.get("probability") or 0), int(engine.get("confidence") or 0), float((plan or {}).get("rr") or 0), float(engine.get("trend_score") or engine.get("score") or 50), str((news or {}).get("sentiment") or "NEUTRAL"))
    strong = strong_buy_engine(engine, news or {}, plan or {})
    return institutional_entry_filter(engine, news or {}, plan or {}, session, news_event, spread, entry_score, strong).get("passed", False)


def build_v42_gold_payload() -> Dict[str, Any]:
    thai = get_thai_gold_v42()
    fx = fetch_xauusd()
    engine = xauusd_engine()
    news = news_ai()

    if news.get("sentiment") == "BULLISH" and engine["signal"] in {"BUY", "STRONG_BUY", "WAIT"}:
        engine["probability"] = min(94, int(engine.get("probability") or 50) + 2)
        engine["confidence"] = min(94, int(engine.get("confidence") or 50) + 2)
    elif news.get("sentiment") == "BEARISH" and engine["signal"] in {"BUY", "STRONG_BUY"}:
        engine["probability"] = max(35, int(engine.get("probability") or 50) - 8)
        engine["confidence"] = max(35, int(engine.get("confidence") or 50) - 8)
        if engine["probability"] <= 80:
            engine["signal"] = "WAIT"

    plan = gold_trade_plan(safe_float(thai.get("bar_sell")), int(engine.get("probability") or 50), engine.get("signal", "WAIT"))
    session = session_filter()
    news_event = high_impact_news_filter()
    spread = spread_filter(thai, fx)
    entry_score = calculate_entry_score(
        int(engine.get("probability") or 0),
        int(engine.get("confidence") or 0),
        float(plan.get("rr") or 0),
        float(engine.get("trend_score") or engine.get("score") or 50),
        str(news.get("sentiment") or "NEUTRAL"),
    )
    strong_buy = strong_buy_engine(engine, news, plan)
    entry_filter = institutional_entry_filter(engine, news, plan, session, news_event, spread, entry_score, strong_buy)
    trailing = smart_trailing_stop(plan, safe_float(thai.get("bar_sell")), engine.get("direction", "BUY"))
    return {
        "ok": bool(thai.get("ok")),
        "version": V42_GOLD_VERSION,
        "time_th": now_th(),
        "thai_gold": thai,
        "xauusd": fx,
        "engine": engine,
        "news": news,
        "session_filter": session,
        "high_impact_news_filter": news_event,
        "spread_filter": spread,
        "trade_plan": plan,
        "entry_score": entry_score,
        "strong_buy": strong_buy,
        "smart_trailing_stop": trailing,
        "entry_filter": entry_filter,
        "push_alert": bool(entry_filter.get("passed")),
        "quality_rule": "V42.3: EntryScore>=80 + London/NY + no high-impact news + spread ok + institutional checks + STRONG BUY engine",
    }


def build_v42_gold_high_conviction_text(payload: Optional[Dict[str, Any]] = None) -> str:
    p = payload or build_v42_gold_payload()
    tg = p.get("thai_gold", {})
    eng = p.get("engine", {})
    plan = p.get("trade_plan", {})
    entries = plan.get("entries", [])
    tps = plan.get("take_profits", [])
    score = p.get("entry_score", {})
    lines = [
        "🔥 V42.3 INSTITUTIONAL HIGH CONVICTION",
        "",
        f"{eng.get('signal', 'WAIT')} GOLD",
        "",
        f"Probability : {eng.get('probability')}%",
        f"Confidence : {eng.get('confidence')}%",
        f"Risk : {eng.get('risk_grade')}",
        f"RR : 1:{fmt_num(plan.get('rr'), 2)}",
        f"Entry Score : {fmt_num(score.get('entry_score'), 2)} ({score.get('entry_grade')})",
        "",
        "เข้าไม้:",
        " / ".join(fmt_num(x, 0) for x in entries) if entries else "N/A",
        "",
        "TP:",
        " / ".join(fmt_num(x, 0) for x in tps) if tps else "N/A",
        "",
        f"SL: {fmt_num(plan.get('stop_loss'), 0)}",
        "",
        "ผ่านทุกเงื่อนไข Institutional" if p.get("push_alert") else "ยังไม่ผ่านทุกเงื่อนไข Institutional",
        f"ราคาอ้างอิงทองแท่งขายออก: {fmt_num(tg.get('bar_sell'), 0)} บาท",
        f"Version : {V42_GOLD_VERSION}",
    ]
    return "\n".join(lines)


def build_v42_gold_text() -> str:
    p = build_v42_gold_payload()
    tg = p.get("thai_gold", {})
    fx = p.get("xauusd", {})
    eng = p.get("engine", {})
    news = p.get("news", {})
    plan = p.get("trade_plan", {})
    filt = p.get("entry_filter", {})
    score = p.get("entry_score", {})
    session = p.get("session_filter", {})
    news_event = p.get("high_impact_news_filter", {})
    spread = p.get("spread_filter", {})
    trailing = p.get("smart_trailing_stop", {})
    strong = p.get("strong_buy", {})
    entries = plan.get("entries", [])
    tps = plan.get("take_profits", [])
    tf = eng.get("timeframes", {})
    tf_line = " | ".join(f"{k}:{v.get('trend','UNKNOWN')}" for k, v in tf.items())
    note = "ราคาเป็นค่าประมาณจาก XAUUSD × USDTHB เพราะแหล่งราคาทองไทยล่ม" if tg.get("is_estimate") else "ใช้ราคาจากแหล่งราคาทองไทย"
    action = filt.get("action") or "ยังไม่เข้าเงื่อนไข"
    title = "🔥 V42.3 GOLD HIGH CONVICTION" if strong.get("passed") else "🏆 V42.3 GOLD INSTITUTIONAL ENTRY FILTER"
    lines = [
        title,
        f"เวลาไทย: {p.get('time_th')}",
        "",
        f"ราคาทองไทย: {note}",
        f"ทองแท่งรับซื้อ: {fmt_num(tg.get('bar_buy'), 0)} บาท",
        f"ทองแท่งขายออก: {fmt_num(tg.get('bar_sell'), 0)} บาท",
        f"ทองรูปพรรณรับซื้อ: {fmt_num(tg.get('ornament_buy'), 0)} บาท",
        f"ทองรูปพรรณขายออก: {fmt_num(tg.get('ornament_sell'), 0)} บาท",
        f"แหล่งข้อมูล: {tg.get('source', 'N/A')}",
        f"อัปเดต: {tg.get('updated_at', 'N/A')}",
        "",
        f"XAUUSD/GC=F: ${fmt_num(fx.get('xauusd'), 2)} | USDTHB: {fmt_num(fx.get('usd_thb'), 2)}",
        f"Signal: {eng.get('signal')} | Decision: {filt.get('decision')} | {action}",
        f"Probability: {eng.get('probability')}% | Confidence: {eng.get('confidence')}% | Risk: {eng.get('risk_grade')} | Regime: {eng.get('regime')}",
        f"Entry Score: {fmt_num(score.get('entry_score'), 2)} | Grade: {score.get('entry_grade')}",
        f"Session: {session.get('session')} | {'ผ่าน' if session.get('allowed') else 'ยังไม่ผ่าน'}",
        f"High Impact News: {news_event.get('decision')}",
        f"Spread: {'ผ่าน' if spread.get('ok') else 'ไม่ผ่าน'} | Thai Spread: {fmt_num(spread.get('thai_spread'), 0)}",
        f"Multi TF: {tf_line}",
        f"Volume Confirm: {'ผ่าน' if eng.get('volume_confirm') else 'ยังไม่ผ่าน'}",
        f"News AI: {news.get('sentiment')} ({news.get('source')})",
        f"RR: {fmt_num(plan.get('rr'), 2)}",
        "",
        "✅ Institutional Entry Filter",
    ]
    for label, ok in (filt.get("checks") or {}).items():
        lines.append(f"{'✅' if ok else '❌'} {label}")
    if filt.get("failed_checks"):
        lines.append("ไม่ผ่าน: " + ", ".join(filt.get("failed_checks", [])))
    lines.append("")
    lines.append("🧩 แผนเข้า/ออกทองไทย")
    if entries and tps:
        lines += [
            f"เข้าไม้ 1: {fmt_num(entries[0], 0)} บาท",
            f"เข้าไม้ 2: {fmt_num(entries[1], 0)} บาท",
            f"เข้าไม้ 3: {fmt_num(entries[2], 0)} บาท",
            f"TP1: {fmt_num(tps[0], 0)} บาท",
            f"TP2: {fmt_num(tps[1], 0)} บาท",
            f"TP3: {fmt_num(tps[2], 0)} บาท",
            f"Stop Loss: {fmt_num(plan.get('stop_loss'), 0)} บาท",
        ]
    else:
        lines.append("ยังไม่พอข้อมูลสำหรับ TP/SL")
    lines += [
        "",
        "🧠 Smart Trailing Stop",
        f"Stage: {trailing.get('stage')} | New SL: {fmt_num(trailing.get('new_sl'), 0)}",
        "",
        "🚨 Auto LINE Push:",
        "พร้อมแจ้งเตือนทันที" if p.get("push_alert") else "ยังไม่แจ้งเตือน เพราะเงื่อนไข Institutional ยังไม่ครบ",
        p.get("quality_rule", ""),
        "",
        f"Version : {V42_GOLD_VERSION}",
    ]
    return "\n".join(lines)



# ============================================================
# V42.4 GOLD INSTITUTIONAL FUND GRADE EXTENSION
# Economic Calendar + DXY/Yield + Order Block + Liquidity Sweep
# Winrate Dashboard + Self Learning
# ============================================================

V42_GOLD_VERSION = "V42.4_GOLD_INSTITUTIONAL_FUND_GRADE_STABLE"

try:
    _V423_BUILD_V42_GOLD_PAYLOAD = build_v42_gold_payload
except Exception:
    _V423_BUILD_V42_GOLD_PAYLOAD = None


def _v424_env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def _v424_env_bool(name: str, default: bool = False) -> bool:
    try:
        return str(os.getenv(name, "true" if default else "false")).lower() in {"1", "true", "yes", "y", "on"}
    except Exception:
        return default


def _v424_latest_close(symbol: str, period: str = "1mo", interval: str = "1d") -> Dict[str, Any]:
    try:
        snap = _market_snapshot(symbol, period=period, interval=interval)
        closes = [safe_float(x) for x in snap.get("closes", []) if safe_float(x) is not None]
        if len(closes) >= 3:
            last = float(closes[-1])
            prev = float(closes[-2])
            base = float(closes[-6]) if len(closes) >= 6 else prev
            trend = "UP" if last > base else "DOWN" if last < base else "FLAT"
            return {"ok": True, "symbol": symbol, "last": last, "prev": prev, "base": base, "trend": trend, "source": snap.get("source")}
    except Exception as e:
        return {"ok": False, "symbol": symbol, "error": str(e)}
    return {"ok": False, "symbol": symbol, "reason": "insufficient_data"}


def economic_calendar_filter() -> Dict[str, Any]:
    """
    V42.4 high impact calendar fail-safe.
    Manual Railway env is supported:
      HIGH_IMPACT_NEWS_ACTIVE=true
      HIGH_IMPACT_NEWS_EVENT=CPI/FOMC/NFP/Powell
      V42_ECON_EVENT_TIME_UTC=2026-06-09T12:30:00+00:00
    If event time is within +/- window minutes, decision becomes WAIT_NEWS.
    """
    window = int(_v424_env_float("HIGH_IMPACT_NEWS_WINDOW_MIN", 30))
    active = _v424_env_bool("HIGH_IMPACT_NEWS_ACTIVE", False)
    event = os.getenv("HIGH_IMPACT_NEWS_EVENT", "CPI/FOMC/NFP/Powell Speech")
    event_time_raw = os.getenv("V42_ECON_EVENT_TIME_UTC", "").strip()
    within_window = False
    minutes_to_event = None
    if event_time_raw:
        try:
            event_time = datetime.fromisoformat(event_time_raw.replace("Z", "+00:00"))
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
            minutes_to_event = (event_time - datetime.now(timezone.utc)).total_seconds() / 60
            within_window = abs(minutes_to_event) <= window
            if within_window:
                active = True
        except Exception:
            pass
    keywords = ["CPI", "FOMC", "NFP", "POWELL", "PCE", "FED", "JOBS"]
    return {
        "ok": not active,
        "blocked": bool(active),
        "event": event if active else None,
        "keywords": keywords,
        "window_minutes": window,
        "minutes_to_event": round(minutes_to_event, 2) if minutes_to_event is not None else None,
        "decision": "WAIT_NEWS" if active else "PASS",
        "rule": "หยุดเทรดก่อน/หลังข่าวแรง เช่น CPI, FOMC, NFP, Powell ภายในหน้าต่างเวลาที่กำหนด",
    }


def dxy_bond_yield_filter(engine: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    V42.4 macro filter for gold.
    If DXY and US10Y both rise, buy-side gold score is penalized.
    """
    engine = engine or {}
    dxy = _v424_latest_close(os.getenv("V42_DXY_SYMBOL", "DX-Y.NYB"), "1mo", "1d")
    yld = _v424_latest_close(os.getenv("V42_YIELD_SYMBOL", "^TNX"), "1mo", "1d")

    # Manual override for markets where yfinance symbol is unavailable on Railway.
    dxy_trend = os.getenv("V42_DXY_TREND", dxy.get("trend", "UNKNOWN")).upper()
    yield_trend = os.getenv("V42_US10Y_TREND", yld.get("trend", "UNKNOWN")).upper()
    bearish_for_gold_buy = dxy_trend == "UP" and yield_trend == "UP"
    buy_side = str(engine.get("direction") or engine.get("signal") or "").upper() in {"BUY", "STRONG_BUY", "CALL", "STRONG_CALL"}
    penalty = int(_v424_env_float("V42_MACRO_BUY_PENALTY", 8)) if bearish_for_gold_buy and buy_side else 0
    return {
        "ok": not bool(penalty),
        "dxy": dxy,
        "us10y": yld,
        "dxy_trend": dxy_trend,
        "yield_trend": yield_trend,
        "bearish_for_gold_buy": bearish_for_gold_buy,
        "buy_side": buy_side,
        "penalty": penalty,
        "decision": "REDUCE_BUY_SCORE" if penalty else "PASS",
        "rule": "ถ้า DXY ขึ้นพร้อม Bond Yield ขึ้น ให้ลดคะแนนฝั่ง Buy ทอง",
    }


def order_block_detection(fx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Lightweight institutional zone detector.
    Uses recent GC=F/XAUUSD closes to estimate demand/supply zone.
    This is decision support, not a guaranteed order block.
    """
    snap = _market_snapshot("GC=F", period="3mo", interval="1d")
    closes = [safe_float(x) for x in snap.get("closes", []) if safe_float(x) is not None]
    if len(closes) < 20:
        return {"ok": False, "reason": "insufficient_data", "source": snap.get("source")}
    recent = [float(x) for x in closes[-30:]]
    last = safe_float((fx or {}).get("xauusd"), recent[-1]) or recent[-1]
    high = max(recent)
    low = min(recent)
    atr_proxy = max(1.0, (high - low) / 6.0)
    demand = [round(low, 2), round(low + atr_proxy * 0.65, 2)]
    supply = [round(high - atr_proxy * 0.65, 2), round(high, 2)]
    in_demand = demand[0] <= last <= demand[1]
    in_supply = supply[0] <= last <= supply[1]
    if in_demand:
        zone_bias = "DEMAND_ZONE"
    elif in_supply:
        zone_bias = "SUPPLY_ZONE"
    else:
        zone_bias = "MID_RANGE"
    return {
        "ok": True,
        "last": round(last, 2),
        "demand_zone": demand,
        "supply_zone": supply,
        "in_demand_zone": in_demand,
        "in_supply_zone": in_supply,
        "zone_bias": zone_bias,
        "source": snap.get("source"),
        "rule": "หา Institutional Demand Zone / Supply Zone แบบ fail-safe จากกรอบราคาล่าสุด",
    }


def liquidity_sweep_detection(fx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Detect simple stop-hunt/fake-breakout behavior from recent closes.
    Conservative: flags only when last close returns back inside recent range.
    """
    snap = _market_snapshot("GC=F", period="1mo", interval="1h")
    closes = [safe_float(x) for x in snap.get("closes", []) if safe_float(x) is not None]
    if len(closes) < 30:
        return {"ok": True, "detected": False, "reason": "insufficient_data", "risk": "UNKNOWN", "source": snap.get("source")}
    values = [float(x) for x in closes]
    prev_range = values[-30:-1]
    last = safe_float((fx or {}).get("xauusd"), values[-1]) or values[-1]
    prev_high = max(prev_range)
    prev_low = min(prev_range)
    buffer = max(0.5, (prev_high - prev_low) * 0.02)
    fake_breakout_high = values[-2] > prev_high + buffer and last < prev_high
    fake_breakdown_low = values[-2] < prev_low - buffer and last > prev_low
    detected = bool(fake_breakout_high or fake_breakdown_low)
    if fake_breakout_high:
        sweep_type = "STOP_HUNT_HIGH_FAKE_BREAKOUT"
    elif fake_breakdown_low:
        sweep_type = "STOP_HUNT_LOW_FAKE_BREAKDOWN"
    else:
        sweep_type = "NONE"
    risk = "HIGH" if detected else "LOW"
    return {
        "ok": not detected,
        "detected": detected,
        "type": sweep_type,
        "risk": risk,
        "last": round(last, 2),
        "prev_high": round(prev_high, 2),
        "prev_low": round(prev_low, 2),
        "source": snap.get("source"),
        "rule": "ตรวจ Stop Hunt / Fake Breakout จากการกลับเข้า range",
    }


def winrate_dashboard(symbol: str = "THAI_GOLD") -> Dict[str, Any]:
    """
    V42.4 forward-test dashboard.
    If realized outcome table is not present, returns sample count safely.
    Optional table supported:
      v42_trade_outcomes(symbol, created_at, pnl, rr)
    """
    import sqlite3
    db_path = os.getenv("DB_PATH", "signals.db")
    result = {
        "ok": True,
        "symbol": symbol,
        "sample_signals": 0,
        "closed_trades": 0,
        "win_rate_pct": None,
        "profit_factor": None,
        "max_drawdown_pct": None,
        "average_rr": None,
        "source": db_path,
        "note": "ยังไม่มีผลปิดออเดอร์จริงพอสำหรับ self learning" 
    }
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM signals WHERE symbol IN (?, ?, ?)", (symbol, "GOLD", "XAUUSD"))
            result["sample_signals"] = int(cur.fetchone()[0] or 0)
        except Exception:
            pass
        try:
            cur.execute("SELECT pnl, rr FROM v42_trade_outcomes WHERE symbol IN (?, ?, ?) ORDER BY created_at", (symbol, "GOLD", "XAUUSD"))
            rows = cur.fetchall()
            pnls = [float(r[0] or 0) for r in rows]
            rrs = [float(r[1] or 0) for r in rows if r[1] is not None]
            if pnls:
                wins = [x for x in pnls if x > 0]
                losses = [abs(x) for x in pnls if x < 0]
                gross_win = sum(wins)
                gross_loss = sum(losses)
                equity = 0.0
                peak = 0.0
                max_dd = 0.0
                for pnl in pnls:
                    equity += pnl
                    peak = max(peak, equity)
                    max_dd = max(max_dd, peak - equity)
                result.update({
                    "closed_trades": len(pnls),
                    "win_rate_pct": round(len(wins) / len(pnls) * 100, 2),
                    "profit_factor": round(gross_win / gross_loss, 2) if gross_loss else None,
                    "max_drawdown_pct": round(max_dd, 2),
                    "average_rr": round(sum(rrs) / len(rrs), 2) if rrs else None,
                    "note": "ใช้ผลปิดออเดอร์จริงจาก v42_trade_outcomes",
                })
        except Exception:
            pass
        conn.close()
    except Exception as e:
        result.update({"ok": False, "error": str(e)})
    return result


def self_learning_adjustment(engine: Dict[str, Any], dashboard: Dict[str, Any]) -> Dict[str, Any]:
    """
    Self learning layer based on real outcome statistics.
    Conservative until at least V42_SELF_LEARNING_MIN_TRADES closed trades.
    """
    min_trades = int(_v424_env_float("V42_SELF_LEARNING_MIN_TRADES", 30))
    closed = int(dashboard.get("closed_trades") or 0)
    win_rate = safe_float(dashboard.get("win_rate_pct"))
    pf = safe_float(dashboard.get("profit_factor"))
    adjustment = 0
    reason = "insufficient_closed_trades"
    if closed >= min_trades and win_rate is not None:
        if win_rate >= 58 and (pf or 0) >= 1.5:
            adjustment = 4
            reason = "positive_edge_confirmed"
        elif win_rate < 48 or ((pf is not None) and pf < 1.1):
            adjustment = -6
            reason = "edge_weak_reduce_score"
        else:
            reason = "neutral_edge"
    return {
        "applied": adjustment != 0,
        "adjustment": adjustment,
        "reason": reason,
        "min_trades": min_trades,
        "closed_trades": closed,
        "rule": "ระบบจำผลชนะ/แพ้จริงแล้วปรับคะแนนแบบอนุรักษ์นิยม",
    }


def institutional_entry_filter_v424(
    engine: Dict[str, Any],
    news: Dict[str, Any],
    plan: Dict[str, Any],
    session: Dict[str, Any],
    econ: Dict[str, Any],
    spread: Dict[str, Any],
    entry_score: Dict[str, Any],
    strong_buy: Dict[str, Any],
    macro: Dict[str, Any],
    order_block: Dict[str, Any],
    liquidity: Dict[str, Any],
) -> Dict[str, Any]:
    base = institutional_entry_filter(engine, news, plan, session, econ, spread, entry_score, strong_buy)
    checks = dict(base.get("checks") or {})
    checks.update({
        "economic_calendar_ok": bool(econ.get("ok")),
        "dxy_yield_filter_ok": not bool(macro.get("penalty")),
        "liquidity_sweep_ok": bool(liquidity.get("ok")),
        "order_block_detected": bool(order_block.get("ok")),
    })
    failed = [k for k, v in checks.items() if not v]
    passed = all(checks.values()) or bool(strong_buy.get("passed"))
    if econ.get("blocked"):
        decision = "WAIT_NEWS"
        action = f"รอข่าวแรงผ่านก่อน: {econ.get('event')}"
    elif macro.get("penalty"):
        decision = "WAIT_MACRO"
        action = "DXY และ Bond Yield หนุนแรงกดดันทองฝั่ง Buy"
    elif not liquidity.get("ok"):
        decision = "WAIT_LIQUIDITY_SWEEP"
        action = "พบความเสี่ยง Stop Hunt / Fake Breakout"
    elif strong_buy.get("passed"):
        decision = "HIGH_CONVICTION_PUSH"
        action = "STRONG BUY ผ่านทุกเงื่อนไข Institutional Fund Grade"
    elif passed:
        decision = "PUSH_ALERT"
        action = "เข้าเงื่อนไขแจ้งเตือนทันที"
    else:
        decision = base.get("decision", "NO_TRADE")
        action = base.get("action", "ยังไม่เข้าเงื่อนไข")
    return {"passed": passed, "decision": decision, "action": action, "checks": checks, "failed_checks": failed}


def build_v42_gold_payload() -> Dict[str, Any]:
    # Start from the latest stable V42.3 engine to preserve all previous fallback behavior.
    if _V423_BUILD_V42_GOLD_PAYLOAD is not None:
        p = _V423_BUILD_V42_GOLD_PAYLOAD()
    else:
        p = {}

    thai = p.get("thai_gold") or get_thai_gold_v42()
    fx = p.get("xauusd") or fetch_xauusd()
    engine = dict(p.get("engine") or xauusd_engine())
    news = p.get("news") or news_ai()
    plan = p.get("trade_plan") or gold_trade_plan(safe_float(thai.get("bar_sell")), int(engine.get("probability") or 50), engine.get("signal", "WAIT"))

    econ = economic_calendar_filter()
    session = session_filter()
    spread = spread_filter(thai, fx)
    macro = dxy_bond_yield_filter(engine)
    order_block = order_block_detection(fx)
    liquidity = liquidity_sweep_detection(fx)
    dashboard = winrate_dashboard("THAI_GOLD")
    learning = self_learning_adjustment(engine, dashboard)

    # Apply macro + self-learning score adjustments conservatively.
    penalty = int(macro.get("penalty") or 0)
    learn_adj = int(learning.get("adjustment") or 0)
    if penalty or learn_adj:
        engine["probability"] = max(25, min(95, int(engine.get("probability") or 50) - penalty + learn_adj))
        engine["confidence"] = max(25, min(95, int(engine.get("confidence") or 50) - penalty + learn_adj))
        engine["macro_adjustment"] = -penalty
        engine["self_learning_adjustment"] = learn_adj
        if engine["probability"] < 80 and str(engine.get("signal")).upper() in {"BUY", "STRONG_BUY"}:
            engine["signal"] = "WAIT"

    # Order block zone adds context, not automatic buy permission.
    if order_block.get("zone_bias") == "DEMAND_ZONE" and str(engine.get("signal")).upper() in {"BUY", "STRONG_BUY", "WAIT"}:
        engine["order_block_context"] = "ใกล้ Demand Zone"
    elif order_block.get("zone_bias") == "SUPPLY_ZONE":
        engine["order_block_context"] = "ใกล้ Supply Zone"

    plan = gold_trade_plan(safe_float(thai.get("bar_sell")), int(engine.get("probability") or 50), engine.get("signal", "WAIT"))
    entry_score = calculate_entry_score(
        int(engine.get("probability") or 0),
        int(engine.get("confidence") or 0),
        float(plan.get("rr") or 0),
        float(engine.get("trend_score") or engine.get("score") or 50),
        str(news.get("sentiment") or "NEUTRAL"),
    )
    strong_buy = strong_buy_engine(engine, news, plan)
    entry_filter = institutional_entry_filter_v424(engine, news, plan, session, econ, spread, entry_score, strong_buy, macro, order_block, liquidity)
    trailing = smart_trailing_stop(plan, safe_float(thai.get("bar_sell")), engine.get("direction", "BUY"))

    p.update({
        "ok": bool(thai.get("ok")),
        "version": V42_GOLD_VERSION,
        "time_th": now_th(),
        "thai_gold": thai,
        "xauusd": fx,
        "engine": engine,
        "news": news,
        "session_filter": session,
        "economic_calendar_filter": econ,
        "high_impact_news_filter": econ,  # backward-compatible key
        "spread_filter": spread,
        "dxy_bond_yield_filter": macro,
        "order_block_detection": order_block,
        "liquidity_sweep_detection": liquidity,
        "winrate_dashboard": dashboard,
        "self_learning": learning,
        "trade_plan": plan,
        "entry_score": entry_score,
        "strong_buy": strong_buy,
        "smart_trailing_stop": trailing,
        "entry_filter": entry_filter,
        "push_alert": bool(entry_filter.get("passed")),
        "quality_rule": "V42.4: Economic Calendar + DXY/Yield + Order Block + Liquidity Sweep + Winrate Dashboard + Self Learning",
    })
    return p


def build_v42_gold_high_conviction_text(payload: Optional[Dict[str, Any]] = None) -> str:
    p = payload or build_v42_gold_payload()
    tg = p.get("thai_gold", {})
    eng = p.get("engine", {})
    plan = p.get("trade_plan", {})
    entries = plan.get("entries", [])
    tps = plan.get("take_profits", [])
    score = p.get("entry_score", {})
    macro = p.get("dxy_bond_yield_filter", {})
    ob = p.get("order_block_detection", {})
    liq = p.get("liquidity_sweep_detection", {})
    dash = p.get("winrate_dashboard", {})
    lines = [
        "🔥 V42.4 INSTITUTIONAL FUND GRADE",
        "",
        f"{eng.get('signal', 'WAIT')} GOLD",
        "",
        f"Probability : {eng.get('probability')}%",
        f"Confidence : {eng.get('confidence')}%",
        f"Risk : {eng.get('risk_grade')}",
        f"RR : 1:{fmt_num(plan.get('rr'), 2)}",
        f"Entry Score : {fmt_num(score.get('entry_score'), 2)} ({score.get('entry_grade')})",
        "",
        f"DXY/Yield: {macro.get('decision')} | DXY {macro.get('dxy_trend')} / Yield {macro.get('yield_trend')}",
        f"Order Block: {ob.get('zone_bias')} | Demand {ob.get('demand_zone')} | Supply {ob.get('supply_zone')}",
        f"Liquidity Sweep: {liq.get('type')} | Risk {liq.get('risk')}",
        f"Winrate: {dash.get('win_rate_pct')}% | PF {dash.get('profit_factor')} | DD {dash.get('max_drawdown_pct')} | Avg RR {dash.get('average_rr')}",
        "",
        "เข้าไม้:",
        " / ".join(fmt_num(x, 0) for x in entries) if entries else "N/A",
        "",
        "TP:",
        " / ".join(fmt_num(x, 0) for x in tps) if tps else "N/A",
        "",
        f"SL: {fmt_num(plan.get('stop_loss'), 0)}",
        "",
        "ผ่านทุกเงื่อนไข Institutional Fund Grade" if p.get("push_alert") else "ยังไม่ผ่านทุกเงื่อนไข Institutional Fund Grade",
        f"ราคาอ้างอิงทองแท่งขายออก: {fmt_num(tg.get('bar_sell'), 0)} บาท",
        f"Version : {V42_GOLD_VERSION}",
    ]
    return "\n".join(lines)


def build_v42_gold_dashboard_text(payload: Optional[Dict[str, Any]] = None) -> str:
    p = payload or build_v42_gold_payload()
    dash = p.get("winrate_dashboard", {})
    learning = p.get("self_learning", {})
    lines = [
        "📊 V42.4 GOLD WINRATE DASHBOARD",
        "",
        f"Sample Signals: {dash.get('sample_signals')}",
        f"Closed Trades: {dash.get('closed_trades')}",
        f"Win Rate: {dash.get('win_rate_pct')}",
        f"Profit Factor: {dash.get('profit_factor')}",
        f"Max DD: {dash.get('max_drawdown_pct')}",
        f"Average RR: {dash.get('average_rr')}",
        "",
        f"Self Learning: {learning.get('reason')} | Adjustment {learning.get('adjustment')}",
        f"Version : {V42_GOLD_VERSION}",
    ]
    return "\n".join(lines)

# ============================================================
# V42.5 GOLD + US EXTENDED HOURS EXPLAINABLE EXTENSION
# Raw/Final Confidence + Explainable AI + US Extended Hours
# Market Breadth SPY/QQQ/VIX
# ============================================================

V42_GOLD_VERSION = "V42.5_GOLD_US_EXTENDED_EXPLAINABLE_STABLE"

try:
    _V424_BUILD_V42_GOLD_PAYLOAD = build_v42_gold_payload
except Exception:
    _V424_BUILD_V42_GOLD_PAYLOAD = None


def _v425_clamp(value: Any, low: float = 0, high: float = 100) -> float:
    v = safe_float(value, low)
    if v is None:
        v = low
    return max(low, min(high, float(v)))


def _v425_percent_change(last: Any, prev: Any) -> Optional[float]:
    a = safe_float(last)
    b = safe_float(prev)
    if a is None or b in (None, 0):
        return None
    return round((a - b) / b * 100, 2)


def _v425_score_from_change(change_pct: Optional[float], bullish_when_up: bool = True) -> float:
    if change_pct is None:
        return 50.0
    s = 50 + (change_pct * 10 if bullish_when_up else -change_pct * 10)
    return round(_v425_clamp(s, 0, 100), 2)


def us_stock_extended_hours(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    V42.5 US Stock Extended Hours.
    Uses yfinance fast_info/info where available. Fails safe when extended data is unavailable.
    Supports pre-market / after-hours tracking for US symbols.
    """
    default_symbols = os.getenv("V42_US_EXTENDED_SYMBOLS", "NVDA,AAPL,TSLA,QQQ,SPY,AMD,META")
    symbols = symbols or [s.strip().upper() for s in default_symbols.split(",") if s.strip()]
    session = "UNKNOWN"
    now_utc = datetime.now(timezone.utc)
    h = now_utc.hour + now_utc.minute / 60.0
    # Approx US Eastern sessions in UTC. DST is approximate but fail-safe.
    if 8 <= h < 13.5:
        session = "PRE_MARKET"
    elif 13.5 <= h < 20:
        session = "REGULAR"
    elif 20 <= h < 24:
        session = "AFTER_HOURS"
    else:
        session = "CLOSED_OR_OVERNIGHT"

    out = {"ok": True, "session": session, "time_utc": now_utc.isoformat(), "items": [], "note": "Extended prices depend on data provider availability."}
    if yf is None:
        out.update({"ok": False, "reason": "yfinance_not_available"})
        return out

    for sym in symbols[:20]:
        item = {"symbol": sym, "ok": False}
        try:
            ticker = yf.Ticker(sym)
            fast = getattr(ticker, "fast_info", {}) or {}
            info = {}
            try:
                info = ticker.info or {}
            except Exception:
                info = {}

            regular = safe_float(
                info.get("regularMarketPrice"),
                safe_float(fast.get("last_price"), safe_float(info.get("previousClose")))
            )
            prev_close = safe_float(info.get("previousClose"), safe_float(fast.get("previous_close")))
            pre = safe_float(info.get("preMarketPrice"))
            post = safe_float(info.get("postMarketPrice"))

            active_price = regular
            active_type = "regular"
            if session == "PRE_MARKET" and pre is not None:
                active_price, active_type = pre, "pre_market"
            elif session == "AFTER_HOURS" and post is not None:
                active_price, active_type = post, "after_hours"

            item.update({
                "ok": regular is not None or active_price is not None,
                "regular_price": regular,
                "previous_close": prev_close,
                "pre_market_price": pre,
                "after_hours_price": post,
                "active_price": active_price,
                "active_type": active_type,
                "active_change_pct": _v425_percent_change(active_price, prev_close),
                "source": "Yahoo Finance/yfinance",
            })
        except Exception as e:
            item.update({"ok": False, "error": str(e)})
        out["items"].append(item)
    return out


def market_breadth_spy_qqq_vix() -> Dict[str, Any]:
    """
    V42.5 Market Breadth using SPY, QQQ and VIX.
    Risk-on if SPY/QQQ rise while VIX falls. Risk-off if SPY/QQQ fall or VIX rises.
    """
    symbols = {"SPY": "SPY", "QQQ": "QQQ", "VIX": "^VIX"}
    data: Dict[str, Any] = {}
    scores = []
    for key, sym in symbols.items():
        snap = _v424_latest_close(sym, "1mo", "1d")
        chg = _v425_percent_change(snap.get("last"), snap.get("prev"))
        snap["change_pct"] = chg
        data[key] = snap
        if key == "VIX":
            scores.append(_v425_score_from_change(chg, bullish_when_up=False))
        else:
            scores.append(_v425_score_from_change(chg, bullish_when_up=True))

    breadth_score = round(sum(scores) / len(scores), 2) if scores else 50.0
    if breadth_score >= 65:
        regime = "RISK_ON"
    elif breadth_score <= 40:
        regime = "RISK_OFF"
    else:
        regime = "NEUTRAL"

    return {
        "ok": True,
        "breadth_score": breadth_score,
        "regime": regime,
        "SPY": data.get("SPY"),
        "QQQ": data.get("QQQ"),
        "VIX": data.get("VIX"),
        "rule": "SPY/QQQ/VIX ใช้ดู risk-on/risk-off เพื่อช่วยกรองหุ้นสหรัฐและทอง",
    }


def explainable_ai_adjustments(raw_engine: Dict[str, Any], final_engine: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    V42.5 Explainable AI: separates raw vs final confidence and lists why score was reduced.
    """
    raw_prob = int(_v425_clamp(raw_engine.get("probability", final_engine.get("probability", 0))))
    raw_conf = int(_v425_clamp(raw_engine.get("confidence", final_engine.get("confidence", 0))))
    final_prob = int(_v425_clamp(final_engine.get("probability", raw_prob)))
    final_conf = int(_v425_clamp(final_engine.get("confidence", raw_conf)))

    reasons: List[Dict[str, Any]] = []
    total_penalty = 0

    macro = payload.get("dxy_bond_yield_filter") or {}
    if macro.get("penalty"):
        p = int(macro.get("penalty") or 0)
        total_penalty += p
        reasons.append({"factor": "DXY + Bond Yield", "penalty": -p, "reason": "DXY และ Bond Yield ขึ้นพร้อมกัน กดคะแนน Buy ทอง"})

    liq = payload.get("liquidity_sweep_detection") or {}
    if liq.get("detected"):
        total_penalty += 10
        reasons.append({"factor": "Liquidity Sweep", "penalty": -10, "reason": "พบ Stop Hunt / Fake Breakout"})

    econ = payload.get("economic_calendar_filter") or payload.get("high_impact_news_filter") or {}
    if econ.get("blocked"):
        total_penalty += 20
        reasons.append({"factor": "High Impact News", "penalty": -20, "reason": f"ใกล้ข่าวแรง {econ.get('event') or ''}".strip()})

    session = payload.get("session_filter") or {}
    if session.get("decision") not in {None, "PASS"} and not session.get("ok", True):
        total_penalty += 5
        reasons.append({"factor": "Session", "penalty": -5, "reason": "อยู่นอก London/New York session"})

    spread = payload.get("spread_filter") or {}
    if spread.get("decision") == "NO_TRADE" or spread.get("ok") is False:
        total_penalty += 8
        reasons.append({"factor": "Spread", "penalty": -8, "reason": "Spread สูงผิดปกติ"})

    entry_filter = payload.get("entry_filter") or {}
    failed = entry_filter.get("failed_checks") or []
    for f in failed[:8]:
        reasons.append({"factor": str(f), "penalty": 0, "reason": f"เงื่อนไข {f} ยังไม่ผ่าน"})

    return {
        "ok": True,
        "raw_probability": raw_prob,
        "raw_confidence": raw_conf,
        "final_probability": final_prob,
        "final_confidence": final_conf,
        "probability_delta": final_prob - raw_prob,
        "confidence_delta": final_conf - raw_conf,
        "total_detected_penalty": -total_penalty,
        "reduction_reasons": reasons,
        "summary": "Final Confidence คือคะแนนหลังผ่านตัวกรอง Institutional; Raw Confidence คือคะแนนก่อนโดนกรอง",
    }


def build_v42_gold_payload() -> Dict[str, Any]:
    """
    V42.5 keeps V42.4 Fund Grade logic, then adds:
    Raw/Final confidence, Explainable AI, US Extended Hours, Market Breadth.
    """
    if _V424_BUILD_V42_GOLD_PAYLOAD is not None:
        p = _V424_BUILD_V42_GOLD_PAYLOAD()
    else:
        p = {}

    raw_engine = dict(p.get("raw_engine") or p.get("engine") or {})
    final_engine = dict(p.get("engine") or raw_engine)

    us_ext = us_stock_extended_hours()
    breadth = market_breadth_spy_qqq_vix()
    explain = explainable_ai_adjustments(raw_engine, final_engine, p)

    # Market breadth context: risk-off can mildly reduce buy-side gold only when existing macro risk is already negative.
    # Do not over-penalize by default; use as context unless env enables.
    apply_breadth_penalty = _v424_env_bool("V42_APPLY_MARKET_BREADTH_TO_GOLD", False)
    if apply_breadth_penalty and breadth.get("regime") == "RISK_OFF" and str(final_engine.get("direction") or final_engine.get("signal")).upper() in {"BUY", "STRONG_BUY"}:
        old_p = int(final_engine.get("probability") or 50)
        old_c = int(final_engine.get("confidence") or 50)
        final_engine["probability"] = max(25, old_p - 5)
        final_engine["confidence"] = max(25, old_c - 5)
        final_engine["market_breadth_adjustment"] = -5
        p["engine"] = final_engine
        explain = explainable_ai_adjustments(raw_engine, final_engine, p)

    p.update({
        "version": V42_GOLD_VERSION,
        "raw_engine": raw_engine,
        "final_engine": final_engine,
        "raw_confidence": {
            "probability": explain.get("raw_probability"),
            "confidence": explain.get("raw_confidence"),
        },
        "final_confidence": {
            "probability": explain.get("final_probability"),
            "confidence": explain.get("final_confidence"),
        },
        "explainable_ai": explain,
        "us_stock_extended_hours": us_ext,
        "market_breadth": breadth,
        "quality_rule": "V42.5: Raw/Final Confidence + Explainable AI + US Extended Hours + SPY/QQQ/VIX Market Breadth",
    })
    return p


def build_v42_gold_explainable_text(payload: Optional[Dict[str, Any]] = None) -> str:
    p = payload or build_v42_gold_payload()
    eng = p.get("engine", {})
    raw = p.get("raw_confidence", {})
    final = p.get("final_confidence", {})
    explain = p.get("explainable_ai", {})
    breadth = p.get("market_breadth", {})
    us_ext = p.get("us_stock_extended_hours", {})
    reasons = explain.get("reduction_reasons") or []

    lines = [
        "🧠 V42.5 GOLD EXPLAINABLE AI",
        "",
        f"Signal: {eng.get('signal', 'WAIT')} | Decision: {(p.get('entry_filter') or {}).get('decision', 'NO_TRADE')}",
        f"Raw Probability: {raw.get('probability')}% | Raw Confidence: {raw.get('confidence')}%",
        f"Final Probability: {final.get('probability')}% | Final Confidence: {final.get('confidence')}%",
        f"Delta: Prob {explain.get('probability_delta')} | Conf {explain.get('confidence_delta')}",
        "",
        "เหตุผลที่ลด/ไม่ผ่าน:",
    ]
    if reasons:
        lines += [f"- {r.get('factor')}: {r.get('reason')} ({r.get('penalty')})" for r in reasons[:10]]
    else:
        lines.append("- ไม่มี penalty สำคัญ")

    lines += [
        "",
        f"Market Breadth: {breadth.get('regime')} | Score {breadth.get('breadth_score')}",
        f"US Extended Session: {us_ext.get('session')}",
        f"Version : {V42_GOLD_VERSION}",
    ]
    return "\n".join(lines)


def build_us_extended_hours_text(symbols: Optional[List[str]] = None) -> str:
    p = us_stock_extended_hours(symbols)
    lines = [
        "🇺🇸 V42.5 US STOCK EXTENDED HOURS",
        f"Session: {p.get('session')}",
        "",
    ]
    for item in p.get("items", [])[:20]:
        lines.append(
            f"{item.get('symbol')} | {item.get('active_type')}: {fmt_num(item.get('active_price'), 2)} | "
            f"Prev: {fmt_num(item.get('previous_close'), 2)} | Change: {fmt_num(item.get('active_change_pct'), 2)}%"
        )
    lines += ["", f"Version : {V42_GOLD_VERSION}"]
    return "\n".join(lines)


def build_market_breadth_text() -> str:
    b = market_breadth_spy_qqq_vix()
    lines = [
        "📊 V42.5 MARKET BREADTH",
        f"Regime: {b.get('regime')} | Score: {b.get('breadth_score')}",
        "",
    ]
    for key in ["SPY", "QQQ", "VIX"]:
        s = b.get(key) or {}
        lines.append(f"{key}: {fmt_num(s.get('last'), 2)} | Change: {fmt_num(s.get('change_pct'), 2)}% | Trend: {s.get('trend')}")
    lines += ["", f"Version : {V42_GOLD_VERSION}"]
    return "\n".join(lines)

# ============================================================
# V42.6 LINE US EXTENDED HOURS COMMAND EXTENSION
# Premarket / After-hours current price + % change in LINE
# ============================================================

V426_US_DEFAULT_SYMBOLS = ["NVDA", "AAPL", "TSLA", "META", "AMD", "QQQ", "SPY"]


def build_us_extended_hours_line_message(symbols: Optional[List[str]] = None) -> str:
    symbols = symbols or V426_US_DEFAULT_SYMBOLS
    payload = us_stock_extended_hours(symbols)
    session = payload.get("session", "UNKNOWN")

    title_map = {
        "PRE_MARKET": "ก่อนตลาดเปิด (Pre-Market)",
        "REGULAR": "ตลาดเปิดปกติ (Regular Session)",
        "AFTER_HOURS": "หลังตลาดปิด (After Hours)",
        "CLOSED_OR_OVERNIGHT": "ตลาดปิด / Overnight",
    }
    session_th = title_map.get(session, session)

    lines = [
        "🇺🇸 ราคาหุ้นสหรัฐ Extended Hours / Pre-After Market",
        f"Session: {session_th}",
        "",
    ]

    items = payload.get("items", []) or []
    if not items:
        lines.append("ยังไม่พบข้อมูลราคา Extended Hours")
    else:
        for item in items:
            sym = item.get("symbol", "N/A")
            active_price = item.get("active_price")
            prev = item.get("previous_close")
            chg = item.get("active_change_pct")
            active_type = item.get("active_type", "regular")

            if active_price is None:
                lines.append(f"{sym}: ยังไม่มีข้อมูล Extended Hours")
                continue

            sign = "+" if chg is not None and float(chg) > 0 else ""
            lines.append(
                f"{sym}: ${fmt_num(active_price, 2)} | {sign}{fmt_num(chg, 2)}% "
                f"| เทียบปิดก่อนหน้า ${fmt_num(prev, 2)} | {active_type}"
            )

    lines += [
        "",
        "คำสั่ง: premarket / afterhours / nvda / aapl / tsla",
        "หมายเหตุ: ข้อมูล Extended Hours ขึ้นกับ Yahoo Finance ว่ามี pre/post market หรือไม่",
        "Version : V42.6.3_LINE_EXTENDED_PRICE_FIRST_STABLE",
    ]
    return "\n".join(lines)


def build_single_us_symbol_line_message(symbol: str) -> str:
    sym = (symbol or "").strip().upper()
    if not sym:
        return build_us_extended_hours_line_message()
    return build_us_extended_hours_line_message([sym])

# ============================================================
# V42.6.2 SHORT EXTENDED HOURS TAIL
# Compact one-line tail for full stock reports in LINE
# ============================================================

def build_us_extended_hours_short_tail(symbol: str) -> str:
    sym = (symbol or "").strip().upper()
    if not sym:
        return ""

    payload = us_stock_extended_hours([sym])
    items = payload.get("items") or []
    if not items:
        return f"🇺🇸 Extended: {sym} ไม่มีข้อมูล Pre/After"

    item = items[0]
    prev = item.get("previous_close")
    pre = item.get("pre_market_price")
    post = item.get("after_hours_price")
    regular = item.get("regular_price")
    session = payload.get("session", "UNKNOWN")

    def _fmt_part(label: str, price: Any) -> str:
        if price is None:
            return f"{label}: N/A"
        chg = _v425_percent_change(price, prev)
        sign = "+" if chg is not None and float(chg) > 0 else ""
        return f"{label}: ${fmt_num(price, 2)} ({sign}{fmt_num(chg, 2)}%)"

    pre_txt = _fmt_part("Pre-market", pre)
    post_txt = _fmt_part("After-hours", post)
    reg_txt = _fmt_part("Regular", regular)

    return (
        f"🇺🇸 Extended Hours [{session}] | "
        f"{pre_txt} | {reg_txt} | {post_txt} | Prev Close: ${fmt_num(prev, 2)}"
    )

# ============================================================
# V42.6.3 EXTENDED PRICE FIRST LINE
# Put current Pre-market / After-hours price directly on first line
# ============================================================

def build_us_extended_hours_first_line(symbol: str) -> str:
    sym = (symbol or "").strip().upper()
    if not sym:
        return ""

    payload = us_stock_extended_hours([sym])
    items = payload.get("items") or []
    session = payload.get("session", "UNKNOWN")

    if not items:
        return f"🇺🇸 {sym}: ยังไม่มีข้อมูล Pre-market / After-hours"

    item = items[0]
    prev = safe_float(item.get("previous_close"))
    regular = safe_float(item.get("regular_price"))
    pre = safe_float(item.get("pre_market_price"))
    post = safe_float(item.get("after_hours_price"))

    if session == "PRE_MARKET" and pre is not None:
        current = pre
        label = "Pre-market"
    elif session == "AFTER_HOURS" and post is not None:
        current = post
        label = "After-hours"
    elif regular is not None:
        current = regular
        label = "Regular"
    elif pre is not None:
        current = pre
        label = "Pre-market"
    elif post is not None:
        current = post
        label = "After-hours"
    else:
        return f"🇺🇸 {sym}: ปิดก่อนหน้า ${fmt_num(prev, 2)} | ยังไม่มีราคา Pre-market / After-hours"

    change = None if prev in (None, 0) else current - prev
    change_pct = None if prev in (None, 0) else (change / prev * 100)

    sign = "+" if change is not None and change > 0 else ""
    sign_pct = "+" if change_pct is not None and change_pct > 0 else ""

    return (
        f"🇺🇸 {sym}: ปิดก่อนหน้า ${fmt_num(prev, 2)} | "
        f"{label} ${fmt_num(current, 2)} | "
        f"{sign}{fmt_num(change, 2)} ({sign_pct}{fmt_num(change_pct, 2)}%)"
    )
