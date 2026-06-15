from dataclasses import asdict
from datetime import datetime, timezone
from math import isnan
from v1414_realtime_price_router.api.realtime_price_router import PriceRouter
from v1413_worldclass_line_os.core.market_brain import get_snapshot, expected_move, trade_plan, entry_score
from v1413_worldclass_line_os.api.priority_router import market_of, time_th

VERSION = "V1419_MASTER_CLEAN_FINAL"

ROUTER = PriceRouter(timeout=2.0)

MAX_AGE = {
    "US": 300,
    "ETF": 300,
    "TH": 900,
    "GOLD": 900,
}

def _num(x, default=None):
    try:
        if x is None:
            return default
        v = float(x)
        if v <= 0:
            return default
        return v
    except Exception:
        return default

def freshness_score(q, market):
    source = str(q.get("source") or "")
    age = q.get("age_seconds")
    stale = bool(q.get("stale"))
    if source == "STATIC_FALLBACK":
        return 0, "STATIC_FALLBACK_REJECT"
    if stale:
        return 30, "STALE_WARNING"
    if age is None:
        # GoldTraders/public and some APIs don't expose tick age. Accept but not perfect.
        return 75 if market == "GOLD" else 65, "NO_TIMESTAMP_ACCEPTED"
    limit = MAX_AGE.get(market, 600)
    if age <= limit:
        return max(70, int(100 - (age / limit) * 25)), "FRESH"
    if age <= limit * 3:
        return 45, "STALE_SOFT"
    return 15, "STALE_HARD"

def force_live_snapshot(symbol):
    s = get_snapshot(symbol)
    market = market_of(s.symbol)
    q = ROUTER.quote(s.symbol)
    fs, fstate = freshness_score(q, market)
    selected = _num(q.get("selected_price"))
    if selected is not None:
        s.price = selected
    prev = _num(q.get("prev_close"))
    if prev is not None:
        s.prev_close = prev
    pre = _num(q.get("premarket"))
    if pre is not None:
        s.premarket = pre
    regular = _num(q.get("regular"))
    if regular is not None:
        s.regular = regular
    after = _num(q.get("afterhours"))
    if after is not None:
        s.afterhours = after

    # expose runtime telemetry
    s._live_quote = q
    s._freshness_score = fs
    s._freshness_state = fstate
    s._market = market
    s._source = q.get("source")
    s._price_mode = q.get("price_mode")
    s._timestamp = q.get("timestamp")
    s._age_seconds = q.get("age_seconds")
    s._stale = q.get("stale")
    return s

def volatility_adjusted_score(s):
    market = getattr(s, "_market", market_of(s.symbol))
    fs = getattr(s, "_freshness_score", 0)
    age_penalty = max(0, (70 - fs) * 0.45)
    atr_pct = (s.atr14 / s.price * 100) if s.price else 0
    vol_bonus = 4 if s.rvol >= 1.2 else (2 if s.rvol >= 1.0 else -2)
    trend_bonus = 4 if s.price > s.ema50 else -2
    risk_bonus = 5 if str(s.risk_grade).startswith("B") else (9 if str(s.risk_grade).startswith("A") else -1)
    raw = s.prob_up * 0.42 + s.confidence * 0.22 + entry_score(s) * 5 + vol_bonus + trend_bonus + risk_bonus
    if atr_pct > 6:
        raw -= 4
    if getattr(s, "_freshness_state", "") in {"STATIC_FALLBACK_REJECT","STALE_HARD"}:
        raw -= 40
    elif getattr(s, "_freshness_state", "") == "STALE_SOFT":
        raw -= 15
    raw -= age_penalty
    return round(max(0, min(100, raw)), 2)

def live_decision(symbol):
    s = force_live_snapshot(symbol)
    market = getattr(s, "_market", market_of(s.symbol))
    fs = getattr(s, "_freshness_score", 0)
    score = volatility_adjusted_score(s)
    em = expected_move(s)
    plan = trade_plan(s)
    state = getattr(s, "_freshness_state", "")
    gate = "REJECT_STALE" if fs < 40 else (
        "NO_TRADE" if s.prob_up < 50 or str(s.view).upper().startswith("BEAR") else (
            "BUY_CANDIDATE" if s.prob_up >= 55 and score >= 60 else "WATCH"
        )
    )
    return {
        "snapshot": s,
        "market": market,
        "freshness_score": fs,
        "freshness_state": state,
        "decision_score": score,
        "gate": gate,
        "expected": em,
        "plan": plan,
        "quote": getattr(s, "_live_quote", {}),
    }

def scan_live_universe(symbols, limit=5):
    rows = []
    for sym in symbols:
        try:
            d = live_decision(sym)
            s = d["snapshot"]
            rows.append({
                "symbol": s.symbol,
                "market": d["market"],
                "price": s.price,
                "prob": s.prob_up,
                "conf": s.confidence,
                "risk": s.risk_grade,
                "view": s.view,
                "gate": d["gate"],
                "score": d["decision_score"],
                "fresh": d["freshness_score"],
                "fresh_state": d["freshness_state"],
                "high_3d": d["expected"]["high_3d"],
                "low_3d": d["expected"]["low_3d"],
                "source": getattr(s, "_source", ""),
                "mode": getattr(s, "_price_mode", ""),
                "reason": s.key_reason,
            })
        except Exception as e:
            rows.append({"symbol": sym, "gate": "ERROR", "score": 0, "fresh": 0, "reason": str(e)})
    buy = sorted([r for r in rows if r.get("gate") == "BUY_CANDIDATE"], key=lambda r: r["score"], reverse=True)[:limit]
    watch = sorted([r for r in rows if r.get("gate") == "WATCH"], key=lambda r: r["score"], reverse=True)[:limit]
    avoid = sorted([r for r in rows if r.get("gate") not in {"BUY_CANDIDATE","WATCH"}], key=lambda r: r.get("score",0))[:limit]
    return {"buy": buy, "watch": watch, "avoid": avoid, "all": rows}
