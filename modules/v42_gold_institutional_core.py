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
# V42.2 GOLD INSTITUTIONAL ENTRY FILTER
# Strict alert layer: alerts only when all high-quality conditions pass.
# This block intentionally overrides selected V42.1 functions while keeping
# all existing fallback price functions intact.
# ============================================================
V42_GOLD_VERSION = "V42.2_GOLD_INSTITUTIONAL_ENTRY_FILTER_STABLE"


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
        # Some XAUUSD sources have no volume. Do not fabricate confirmation.
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
    }


def gold_trade_plan(bar_sell: Optional[float], prob: int, signal: str) -> Dict[str, Any]:
    if not bar_sell:
        return {}
    # Conservative baht-gold plan designed to keep RR above 1:2.
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


def institutional_entry_filter(engine: Dict[str, Any], news: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
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
    }
    passed = all(checks.values())
    failed = [k for k, v in checks.items() if not v]
    if passed:
        decision = "PUSH_ALERT"
        action = "เข้าเงื่อนไขแจ้งเตือนทันที"
    elif signal in {"BUY", "STRONG_BUY", "SELL"} and probability > 75:
        decision = "WATCH_ONLY"
        action = "เฝ้าดู รอเงื่อนไขครบ"
    else:
        decision = "NO_TRADE"
        action = "ยังไม่เข้าเงื่อนไข"
    return {"passed": passed, "decision": decision, "action": action, "checks": checks, "failed_checks": failed}


def should_push_alert(engine: Dict[str, Any], news: Optional[Dict[str, Any]] = None, plan: Optional[Dict[str, Any]] = None) -> bool:
    return institutional_entry_filter(engine, news or {}, plan or {}).get("passed", False)


def build_v42_gold_payload() -> Dict[str, Any]:
    thai = get_thai_gold_v42()
    fx = fetch_xauusd()
    engine = xauusd_engine()
    news = news_ai()

    # News adjustment: do not allow bullish signal if news is clearly negative.
    if news.get("sentiment") == "BULLISH" and engine["signal"] in {"BUY", "STRONG_BUY", "WAIT"}:
        engine["probability"] = min(94, int(engine.get("probability") or 50) + 2)
        engine["confidence"] = min(94, int(engine.get("confidence") or 50) + 2)
    elif news.get("sentiment") == "BEARISH" and engine["signal"] in {"BUY", "STRONG_BUY"}:
        engine["probability"] = max(35, int(engine.get("probability") or 50) - 8)
        engine["confidence"] = max(35, int(engine.get("confidence") or 50) - 8)
        if engine["probability"] <= 80:
            engine["signal"] = "WAIT"

    plan = gold_trade_plan(safe_float(thai.get("bar_sell")), int(engine.get("probability") or 50), engine.get("signal", "WAIT"))
    entry_filter = institutional_entry_filter(engine, news, plan)
    return {
        "ok": bool(thai.get("ok")),
        "version": V42_GOLD_VERSION,
        "time_th": now_th(),
        "thai_gold": thai,
        "xauusd": fx,
        "engine": engine,
        "news": news,
        "trade_plan": plan,
        "entry_filter": entry_filter,
        "push_alert": bool(entry_filter.get("passed")),
        "quality_rule": "V42.2: Multi TF aligned + Volume confirm + Probability >80 + Confidence >85 + News not bearish + RR >2 + Risk A/B+",
    }


def build_v42_gold_text() -> str:
    p = build_v42_gold_payload()
    tg = p.get("thai_gold", {})
    fx = p.get("xauusd", {})
    eng = p.get("engine", {})
    news = p.get("news", {})
    plan = p.get("trade_plan", {})
    filt = p.get("entry_filter", {})
    entries = plan.get("entries", [])
    tps = plan.get("take_profits", [])
    tf = eng.get("timeframes", {})
    tf_line = " | ".join(f"{k}:{v.get('trend','UNKNOWN')}" for k, v in tf.items())
    note = "ราคาเป็นค่าประมาณจาก XAUUSD × USDTHB เพราะแหล่งราคาทองไทยล่ม" if tg.get("is_estimate") else "ใช้ราคาจากแหล่งราคาทองไทย"
    action = filt.get("action") or "ยังไม่เข้าเงื่อนไข"
    lines = [
        "🏆 V42.2 GOLD INSTITUTIONAL ENTRY FILTER",
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
        "🚨 Auto LINE Push:",
        "พร้อมแจ้งเตือนทันที" if p.get("push_alert") else "ยังไม่แจ้งเตือน เพราะเงื่อนไข Institutional ยังไม่ครบ",
        p.get("quality_rule", ""),
        "",
        f"Version : {V42_GOLD_VERSION}",
    ]
    return "\n".join(lines)
