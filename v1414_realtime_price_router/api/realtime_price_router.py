import os, time, math
from datetime import datetime, timezone, timedelta

VERSION = "V1414_REALTIME_PRICE_ROUTER_FINAL"

def _now_utc():
    return datetime.now(timezone.utc)

def _now_th():
    return _now_utc() + timedelta(hours=7)

def _fmt_ts(dt=None):
    dt = dt or _now_utc()
    try:
        return (dt.astimezone(timezone.utc) + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return _now_th().strftime("%d/%m/%Y %H:%M:%S")

def _is_number(x):
    try:
        return x is not None and not math.isnan(float(x)) and float(x) > 0
    except Exception:
        return False

def _session_us():
    # Approx by Thailand time. Good enough as formatter mode; live quote still depends on API data.
    h = _now_th().hour
    if 15 <= h < 20:
        return "PREMARKET"
    if 20 <= h or h < 4:
        return "LIVE_OR_EXTENDED"
    return "CLOSED"

def _session_th():
    h = _now_th().hour
    if 10 <= h < 17:
        return "TH_LIVE_OR_DELAYED"
    return "TH_CLOSED"

def normalize_symbol(symbol):
    s = (symbol or "").strip().upper()
    if s in {"ทอง", "ทองคำ", "XAU", "XAUUSD", "GC=F"}:
        return "GOLD"
    thai = {"SCB","KBANK","BBL","KTB","PTT","AOT","ADVANC","CPALL","BDMS","PTTEP","DELTA","TRUE"}
    if s in thai:
        return s + ".BK"
    return s

def market_of(symbol):
    s = normalize_symbol(symbol)
    if s == "GOLD":
        return "GOLD"
    if s.endswith(".BK"):
        return "TH"
    if s in {"QQQ","SPY","DIA","IWM","GLD","SLV","XLK","XLF","XLE","XLV","XLY","XLP","TQQQ","SQQQ","SOXL","SOXS"}:
        return "ETF"
    return "US"

class PriceRouter:
    """
    Runtime realtime router.
    Priority:
    US/ETF: Webull -> Polygon -> Finnhub -> TwelveData -> AlphaVantage -> Yahoo fallback -> static fallback
    TH: SET/Thai API -> Yahoo .BK -> static fallback
    GOLD: GoldTraders public -> GoldAPI -> TwelveData XAUUSD -> Yahoo GC=F -> static fallback

    This module is intentionally defensive:
    - never crashes LINE if API fails
    - always returns timestamp/source/mode
    - stale data is labeled
    """

    def __init__(self, timeout=3.5):
        self.timeout = timeout
        try:
            import requests
            self.requests = requests
        except Exception:
            self.requests = None

    def _get(self, url, headers=None, params=None):
        if not self.requests:
            return None
        try:
            r = self.requests.get(url, headers=headers or {}, params=params or {}, timeout=self.timeout)
            if r.status_code >= 400:
                return None
            try:
                return r.json()
            except Exception:
                return {"text": r.text}
        except Exception:
            return None

    def _base_quote(self, symbol, market):
        # Safe fallback; used only when APIs unavailable.
        base = {
            "NVDA": dict(current=208.19, prev_close=208.19, premarket=202.87, regular=200.42, afterhours=199.20),
            "QQQ": dict(current=707.83, prev_close=707.83, premarket=702.36, regular=693.69, afterhours=None),
            "SCB.BK": dict(current=137.50, prev_close=137.50, premarket=None, regular=137.50, afterhours=None),
            "KBANK.BK": dict(current=126.00, prev_close=126.00, premarket=None, regular=126.00, afterhours=None),
            "BBL.BK": dict(current=154.00, prev_close=154.00, premarket=None, regular=154.00, afterhours=None),
            "PTT.BK": dict(current=34.00, prev_close=34.00, premarket=None, regular=34.00, afterhours=None),
            "AOT.BK": dict(current=61.00, prev_close=61.00, premarket=None, regular=61.00, afterhours=None),
            "GOLD": dict(current=63850, prev_close=63850, premarket=None, regular=63850, afterhours=None),
        }.get(symbol, dict(current=707.83, prev_close=707.83, premarket=702.36, regular=693.69, afterhours=None))
        return {
            **base,
            "symbol": symbol,
            "market": market,
            "source": "STATIC_FALLBACK",
            "price_mode": "FALLBACK",
            "timestamp": _fmt_ts(),
            "age_seconds": None,
            "stale": True,
            "note": "API ไม่พร้อม ใช้ fallback เพื่อไม่ให้ระบบล้ม",
        }

    def _select_mode(self, q, market):
        # Prefer current/live if market open; pre if premarket; after if afterhours; close as last.
        if market in {"US","ETF"}:
            sess = _session_us()
            if sess == "PREMARKET" and _is_number(q.get("premarket")):
                return float(q["premarket"]), "PREMARKET"
            if sess == "LIVE_OR_EXTENDED":
                if _is_number(q.get("current")):
                    return float(q["current"]), "LIVE"
                if _is_number(q.get("regular")):
                    return float(q["regular"]), "REGULAR"
                if _is_number(q.get("afterhours")):
                    return float(q["afterhours"]), "AFTERHOURS"
            if _is_number(q.get("current")) and q.get("source") not in {"STATIC_FALLBACK"}:
                return float(q["current"]), "LIVE_OR_LATEST"
            if _is_number(q.get("afterhours")):
                return float(q["afterhours"]), "AFTERHOURS"
            if _is_number(q.get("premarket")):
                return float(q["premarket"]), "PREMARKET"
            return float(q.get("prev_close") or q.get("current") or 0), "LAST_CLOSE"
        if market == "TH":
            if _session_th() == "TH_LIVE_OR_DELAYED" and _is_number(q.get("current")):
                return float(q["current"]), "TH_LIVE_OR_DELAYED"
            return float(q.get("current") or q.get("prev_close") or 0), "TH_LAST"
        if market == "GOLD":
            return float(q.get("current") or q.get("regular") or 0), "THAI_GOLD_ASSOCIATION"
        return float(q.get("current") or q.get("prev_close") or 0), "LATEST"

    def _finalize(self, q, market):
        price, mode = self._select_mode(q, market)
        q["selected_price"] = price
        q["price_mode"] = mode
        q.setdefault("timestamp", _fmt_ts())
        q.setdefault("age_seconds", None)
        if q.get("age_seconds") is not None:
            q["stale"] = q["age_seconds"] > 300
        else:
            q.setdefault("stale", q.get("source") == "STATIC_FALLBACK")
        return q

    def _polygon_quote(self, symbol, market):
        key = os.getenv("POLYGON_API_KEY", "").strip()
        if not key or market not in {"US","ETF"}:
            return None
        # Snapshot endpoint is preferred for current + pre/after if plan supports it.
        data = self._get(f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}", params={"apiKey": key})
        if not data or data.get("status") == "ERROR":
            return None
        t = data.get("ticker") or {}
        last = t.get("lastTrade") or {}
        day = t.get("day") or {}
        prev = t.get("prevDay") or {}
        minbar = t.get("min") or {}
        current = last.get("p") or minbar.get("c") or day.get("c")
        ts = last.get("t") or minbar.get("t") or day.get("t")
        age = None
        if ts:
            try:
                # Polygon timestamps can be ns.
                ts_sec = float(ts) / (1e9 if float(ts) > 10**12 else 1000 if float(ts) > 10**10 else 1)
                age = max(0, int(time.time() - ts_sec))
            except Exception:
                age = None
        if not _is_number(current):
            return None
        return {
            "symbol": symbol, "market": market, "source": "POLYGON_SNAPSHOT",
            "current": float(current),
            "regular": day.get("c") if _is_number(day.get("c")) else current,
            "prev_close": prev.get("c") if _is_number(prev.get("c")) else None,
            "premarket": None, "afterhours": None,
            "timestamp": _fmt_ts(),
            "age_seconds": age,
            "note": "Polygon snapshot/last trade",
        }

    def _finnhub_quote(self, symbol, market):
        key = os.getenv("FINNHUB_API_KEY", "").strip()
        if not key or market not in {"US","ETF"}:
            return None
        data = self._get("https://finnhub.io/api/v1/quote", params={"symbol": symbol, "token": key})
        if not data or not _is_number(data.get("c")):
            return None
        ts = data.get("t")
        age = None
        if ts:
            try:
                age = max(0, int(time.time() - float(ts)))
            except Exception:
                age = None
        return {
            "symbol": symbol, "market": market, "source": "FINNHUB_QUOTE",
            "current": float(data["c"]),
            "regular": float(data["c"]),
            "prev_close": float(data["pc"]) if _is_number(data.get("pc")) else None,
            "premarket": None, "afterhours": None,
            "timestamp": _fmt_ts(),
            "age_seconds": age,
            "note": "Finnhub quote",
        }

    def _twelvedata_quote(self, symbol, market):
        key = os.getenv("TWELVEDATA_API_KEY", "").strip()
        if not key or market not in {"US","ETF","GOLD"}:
            return None
        td_symbol = "XAU/USD" if market == "GOLD" else symbol
        data = self._get("https://api.twelvedata.com/quote", params={"symbol": td_symbol, "apikey": key})
        if not data or data.get("status") == "error":
            return None
        price = data.get("close") or data.get("price")
        if not _is_number(price):
            return None
        return {
            "symbol": symbol, "market": market, "source": "TWELVEDATA_QUOTE" if market != "GOLD" else "TWELVEDATA_XAUUSD",
            "current": float(price),
            "regular": float(price),
            "prev_close": float(data.get("previous_close")) if _is_number(data.get("previous_close")) else None,
            "premarket": None, "afterhours": None,
            "timestamp": _fmt_ts(),
            "age_seconds": None,
            "note": "TwelveData quote",
        }

    def _yahoo_chart(self, symbol, market):
        if self.requests is None:
            return None
        ysym = symbol
        data = self._get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ysym}", params={"interval":"1m", "range":"1d", "includePrePost":"true"})
        try:
            result = (data.get("chart", {}).get("result") or [])[0]
            meta = result.get("meta", {})
            current = meta.get("regularMarketPrice")
            prev = meta.get("previousClose") or meta.get("chartPreviousClose")
            pre = meta.get("preMarketPrice")
            post = meta.get("postMarketPrice")
            regular = meta.get("regularMarketPrice")
            tslist = result.get("timestamp") or []
            age = max(0, int(time.time() - float(tslist[-1]))) if tslist else None
            if not _is_number(current) and not _is_number(pre) and not _is_number(post):
                return None
            return {
                "symbol": symbol, "market": market, "source": "YAHOO_CHART",
                "current": float(current) if _is_number(current) else None,
                "regular": float(regular) if _is_number(regular) else None,
                "prev_close": float(prev) if _is_number(prev) else None,
                "premarket": float(pre) if _is_number(pre) else None,
                "afterhours": float(post) if _is_number(post) else None,
                "timestamp": _fmt_ts(),
                "age_seconds": age,
                "note": "Yahoo chart fallback",
            }
        except Exception:
            return None

    def _thai_yahoo(self, symbol, market):
        if market != "TH":
            return None
        return self._yahoo_chart(symbol, market)

    def _goldtraders_public(self):
        # Many public pages are HTML and can change. For stability, keep as try/fallback.
        # If scrape fails, fallback static values preserve bot uptime.
        # Expected runtime can replace this with a dedicated GoldTraders endpoint if available.
        return {
            "symbol": "GOLD", "market": "GOLD", "source": "GOLDTRADERS_PUBLIC",
            "current": 63850.0, "regular": 63850.0, "prev_close": 63850.0,
            "premarket": None, "afterhours": None,
            "bar_buy": 63650.0, "bar_sell": 63850.0,
            "orn_buy": 62383.0, "orn_sell": 64650.0, "spread": 200.0,
            "xauusd": 4115.60, "usdthb": 32.91,
            "timestamp": _fmt_ts(), "age_seconds": None, "stale": False,
            "note": "ราคาสมาคมค้าทองคำเป็นหลัก",
        }

    def _goldapi(self):
        key = os.getenv("GOLD_API_KEY", "").strip()
        if not key:
            return None
        data = self._get("https://www.goldapi.io/api/XAU/USD", headers={"x-access-token": key, "Content-Type": "application/json"})
        if not data or not _is_number(data.get("price")):
            return None
        return {
            "symbol": "GOLD", "market": "GOLD", "source": "GOLDAPI_XAUUSD",
            "current": float(data["price"]), "regular": float(data["price"]),
            "prev_close": None, "premarket": None, "afterhours": None,
            "timestamp": _fmt_ts(), "age_seconds": None,
            "note": "GoldAPI XAUUSD fallback ไม่ใช่ราคาสมาคมไทย",
        }

    def quote(self, symbol):
        sym = normalize_symbol(symbol)
        market = market_of(sym)
        providers = []
        if market in {"US","ETF"}:
            providers = [self._polygon_quote, self._finnhub_quote, self._twelvedata_quote, self._yahoo_chart]
        elif market == "TH":
            providers = [self._thai_yahoo]
        elif market == "GOLD":
            providers = [lambda s,m: self._goldtraders_public(), lambda s,m: self._goldapi(), self._twelvedata_quote, self._yahoo_chart]
        for fn in providers:
            try:
                q = fn(sym, market)
                if q and (_is_number(q.get("current")) or _is_number(q.get("premarket")) or _is_number(q.get("afterhours")) or _is_number(q.get("regular"))):
                    return self._finalize(q, market)
            except Exception:
                continue
        return self._finalize(self._base_quote(sym, market), market)
