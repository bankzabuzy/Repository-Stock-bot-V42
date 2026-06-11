
# V43-V50 WORLD CLASS INSTITUTIONAL STACK
# Portfolio Manager → Relative Strength → Options Flow → Dark Pool
# Macro Engine → Monte Carlo → Self Learning → Portfolio Optimizer
# Fail-safe design: all functions return structured payloads and should not crash the worker.

from __future__ import annotations

import os
import math
import random
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

try:
    import yfinance as yf  # type: ignore
except Exception:
    yf = None

V50_VERSION = "V50_WORLD_CLASS_INSTITUTIONAL_STACK_STABLE"

DEFAULT_UNIVERSE = ["NVDA", "AAPL", "TSLA", "META", "AMD", "TSM", "QQQ", "SPY", "MSFT", "GOOGL"]
SECTOR_MAP = {
    "NVDA": "Technology",
    "AAPL": "Technology",
    "TSLA": "Consumer Discretionary",
    "META": "Communication Services",
    "AMD": "Technology",
    "TSM": "Semiconductors",
    "QQQ": "ETF Nasdaq",
    "SPY": "ETF Broad Market",
    "MSFT": "Technology",
    "GOOGL": "Communication Services",
    "GOLD": "Gold",
    "THAI_GOLD": "Gold",
    "XAUUSD": "Gold",
}


def _now_th() -> str:
    return datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")


def _safe_float(x: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if x is None:
            return default
        if isinstance(x, str):
            x = x.replace(",", "").replace("$", "").replace("฿", "").strip()
            if not x or x.upper() in {"N/A", "NONE", "NULL"}:
                return default
        return float(x)
    except Exception:
        return default


def _clamp(x: Any, low: float = 0, high: float = 100) -> float:
    v = _safe_float(x, low)
    if v is None:
        v = low
    return max(low, min(high, float(v)))


def _db_path() -> str:
    return os.getenv("DB_PATH", "signals.db")


def _market_snapshot(symbol: str, period: str = "3mo", interval: str = "1d") -> Dict[str, Any]:
    if yf is None:
        return {"ok": False, "symbol": symbol, "reason": "yfinance_not_available", "closes": []}
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True, threads=False)
        if df is None or df.empty:
            return {"ok": False, "symbol": symbol, "reason": "no_data", "closes": []}
        closes = [float(x) for x in df["Close"].dropna().tail(120).values]
        return {"ok": bool(closes), "symbol": symbol, "closes": closes, "last": closes[-1] if closes else None, "source": "Yahoo Finance"}
    except Exception as e:
        return {"ok": False, "symbol": symbol, "reason": str(e), "closes": []}


def _return_pct(closes: List[float], lookback: int = 20) -> float:
    if not closes or len(closes) <= lookback:
        return 0.0
    base = closes[-lookback]
    if base == 0:
        return 0.0
    return (closes[-1] - base) / base * 100


def _volatility_pct(closes: List[float], lookback: int = 20) -> float:
    if len(closes) < lookback + 1:
        return 3.0
    rets = []
    for i in range(-lookback, 0):
        prev = closes[i-1]
        if prev:
            rets.append((closes[i] - prev) / prev)
    if not rets:
        return 3.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / max(1, len(rets)-1)
    return math.sqrt(var) * math.sqrt(252) * 100


def _latest_signals(limit: int = 100) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        conn = sqlite3.connect(_db_path())
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # Try common signals table.
        cur.execute("SELECT * FROM signals ORDER BY rowid DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
    except Exception:
        rows = []
    return rows


def _portfolio_positions_from_env() -> List[Dict[str, Any]]:
    # Format: NVDA:8,TSM:6,QQQ:12,GOLD:10
    raw = os.getenv("V50_POSITIONS", "NVDA:8,TSM:6,QQQ:12,THAI_GOLD:10")
    out = []
    for part in raw.split(","):
        if ":" in part:
            sym, w = part.split(":", 1)
            out.append({"symbol": sym.strip().upper(), "weight_pct": _safe_float(w, 0) or 0})
    return out


# V43 Portfolio Manager Layer
def v43_portfolio_manager() -> Dict[str, Any]:
    positions = _portfolio_positions_from_env()
    max_heat = _safe_float(os.getenv("V43_MAX_PORTFOLIO_HEAT", "40"), 40) or 40
    max_sector = _safe_float(os.getenv("V43_MAX_SECTOR_EXPOSURE", "35"), 35) or 35

    heat = round(sum(abs(_safe_float(p.get("weight_pct"), 0) or 0) for p in positions), 2)
    sector: Dict[str, float] = {}
    for p in positions:
        sym = str(p.get("symbol", "")).upper()
        sec = SECTOR_MAP.get(sym, "Other")
        sector[sec] = round(sector.get(sec, 0) + float(p.get("weight_pct") or 0), 2)

    sector_breaches = {k: v for k, v in sector.items() if abs(v) > max_sector}
    decision = "NO_NEW_POSITION" if heat > max_heat or sector_breaches else "ALLOW"
    return {
        "version": "V43_PORTFOLIO_MANAGER_LAYER",
        "ok": True,
        "positions": positions,
        "portfolio_heat_pct": heat,
        "max_heat_pct": max_heat,
        "sector_exposure": sector,
        "max_sector_exposure_pct": max_sector,
        "sector_breaches": sector_breaches,
        "decision": decision,
        "rule": "จำกัด Portfolio Heat และ Sector Exposure ก่อนเปิดออเดอร์ใหม่",
    }


# V44 Relative Strength Engine
def v44_relative_strength(symbols: Optional[List[str]] = None, benchmark: str = "SPY") -> Dict[str, Any]:
    symbols = symbols or DEFAULT_UNIVERSE
    bench = _market_snapshot(benchmark, "6mo", "1d")
    bench_ret = _return_pct(bench.get("closes", []), 20)
    items = []
    for sym in symbols:
        snap = _market_snapshot(sym, "6mo", "1d")
        ret20 = _return_pct(snap.get("closes", []), 20)
        ret60 = _return_pct(snap.get("closes", []), 60)
        rs = ret20 - bench_ret
        score = _clamp(50 + rs * 2 + ret60 * 0.4)
        items.append({
            "symbol": sym,
            "ok": snap.get("ok"),
            "ret20_pct": round(ret20, 2),
            "ret60_pct": round(ret60, 2),
            "benchmark": benchmark,
            "benchmark_ret20_pct": round(bench_ret, 2),
            "relative_strength_pct": round(rs, 2),
            "rs_score": round(score, 2),
            "rank_bias": "LEADER" if score >= 70 else "LAGGARD" if score <= 40 else "NEUTRAL",
        })
    items.sort(key=lambda x: x.get("rs_score", 0), reverse=True)
    return {"version": "V44_RELATIVE_STRENGTH_ENGINE", "ok": True, "benchmark": benchmark, "items": items}


# V45 Options Flow Engine (free/fail-safe proxy)
def v45_options_flow(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    symbols = symbols or DEFAULT_UNIVERSE
    items = []
    for sym in symbols:
        # Free fallback proxy: no paid options feed. Uses env override or price momentum as proxy.
        override = os.getenv(f"V45_OPTIONS_FLOW_{sym}", "").upper()
        snap = _market_snapshot(sym, "1mo", "1d")
        mom = _return_pct(snap.get("closes", []), 5)
        if override in {"BULLISH", "BEARISH", "NEUTRAL"}:
            bias = override
        elif mom > 3:
            bias = "BULLISH_PROXY"
        elif mom < -3:
            bias = "BEARISH_PROXY"
        else:
            bias = "NEUTRAL_PROXY"
        score = 60 + mom * 3 if "BULLISH" in bias else 40 + mom * 3 if "BEARISH" in bias else 50
        items.append({
            "symbol": sym,
            "bias": bias,
            "options_flow_score": round(_clamp(score), 2),
            "source": "free_proxy_env_or_momentum",
            "note": "ต่อ API options flow จริงได้ภายหลัง เช่น unusual activity / OI / IV",
        })
    return {"version": "V45_OPTIONS_FLOW_ENGINE", "ok": True, "items": items}


# V46 Dark Pool Engine (free/fail-safe proxy)
def v46_dark_pool(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    symbols = symbols or DEFAULT_UNIVERSE
    items = []
    for sym in symbols:
        override = _safe_float(os.getenv(f"V46_DARK_POOL_SCORE_{sym}"))
        if override is not None:
            score = override
            source = "env_override"
        else:
            snap = _market_snapshot(sym, "1mo", "1d")
            vol = _volatility_pct(snap.get("closes", []), 10)
            ret = _return_pct(snap.get("closes", []), 10)
            score = _clamp(50 + ret * 1.5 - max(0, vol - 60) * 0.2)
            source = "free_proxy_price_volume_unavailable"
        items.append({
            "symbol": sym,
            "dark_pool_score": round(score, 2),
            "bias": "ACCUMULATION_PROXY" if score >= 65 else "DISTRIBUTION_PROXY" if score <= 35 else "NEUTRAL_PROXY",
            "source": source,
            "note": "ไม่มี dark-pool feed ฟรีจริง ใช้ proxy และรองรับ env override",
        })
    return {"version": "V46_DARK_POOL_ENGINE", "ok": True, "items": items}


# V47 Macro Engine
def v47_macro_engine() -> Dict[str, Any]:
    symbols = {"DXY": "DX-Y.NYB", "US10Y": "^TNX", "VIX": "^VIX", "GOLD": "GC=F", "OIL": "CL=F", "SPY": "SPY", "QQQ": "QQQ"}
    data = {}
    score_parts = []
    for key, sym in symbols.items():
        snap = _market_snapshot(sym, "3mo", "1d")
        ret = _return_pct(snap.get("closes", []), 10)
        data[key] = {"symbol": sym, "ok": snap.get("ok"), "last": snap.get("last"), "ret10_pct": round(ret, 2)}
    # Risk regime heuristic
    spy = data["SPY"]["ret10_pct"]
    qqq = data["QQQ"]["ret10_pct"]
    vix = data["VIX"]["ret10_pct"]
    dxy = data["DXY"]["ret10_pct"]
    yld = data["US10Y"]["ret10_pct"]
    risk_score = 50 + spy * 2 + qqq * 1.5 - vix * 1.5 - max(0, dxy) - max(0, yld) * 0.5
    risk_score = round(_clamp(risk_score), 2)
    regime = "RISK_ON" if risk_score >= 65 else "RISK_OFF" if risk_score <= 40 else "MIXED"
    return {
        "version": "V47_MACRO_ENGINE",
        "ok": True,
        "risk_score": risk_score,
        "macro_regime": regime,
        "data": data,
        "rule": "DXY, Yield, VIX, SPY, QQQ, Gold, Oil เพื่อประเมิน Risk ON/OFF",
    }


# V48 Monte Carlo Stress Test
def v48_monte_carlo(symbol: str = "PORTFOLIO", trials: int = 2000, win_rate: float = 0.52, avg_win_r: float = 1.6, avg_loss_r: float = 1.0, trades: int = 100) -> Dict[str, Any]:
    trials = int(min(max(trials, 100), 10000))
    random.seed(42)
    finals = []
    max_dds = []
    for _ in range(trials):
        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for _t in range(trades):
            if random.random() < win_rate:
                r = random.uniform(avg_win_r * 0.5, avg_win_r * 1.5)
            else:
                r = -random.uniform(avg_loss_r * 0.5, avg_loss_r * 1.5)
            equity += r
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        finals.append(equity)
        max_dds.append(max_dd)
    finals_sorted = sorted(finals)
    dd_sorted = sorted(max_dds)
    def pct(vals, q):
        idx = min(len(vals)-1, max(0, int(len(vals)*q)))
        return round(vals[idx], 2)
    return {
        "version": "V48_MONTE_CARLO_STRESS_TEST",
        "ok": True,
        "symbol": symbol,
        "trials": trials,
        "trades_per_trial": trades,
        "assumptions": {"win_rate": win_rate, "avg_win_r": avg_win_r, "avg_loss_r": avg_loss_r},
        "expected_final_r": round(sum(finals)/len(finals), 2),
        "p05_final_r": pct(finals_sorted, 0.05),
        "p50_final_r": pct(finals_sorted, 0.50),
        "p95_final_r": pct(finals_sorted, 0.95),
        "median_max_dd_r": pct(dd_sorted, 0.50),
        "p95_max_dd_r": pct(dd_sorted, 0.95),
        "risk_of_ruin_proxy_pct": round(sum(1 for x in finals if x < -20) / len(finals) * 100, 2),
    }


# V49 Self Learning AI
def v49_self_learning() -> Dict[str, Any]:
    rows = _latest_signals(500)
    # Use V1300.1.7 performance if available.
    closed = 0
    wins = 0
    try:
        conn = sqlite3.connect(_db_path())
        cur = conn.cursor()
        cur.execute("SELECT pnl_r, signal_grade FROM v427_trade_journal WHERE status='CLOSED'")
        data = cur.fetchall()
        conn.close()
        closed = len(data)
        wins = sum(1 for pnl, _grade in data if pnl and float(pnl) > 0)
    except Exception:
        data = []
    win_rate = round(wins / closed * 100, 2) if closed else None
    adjustment = 0
    if closed >= 30 and win_rate is not None:
        if win_rate >= 58:
            adjustment = 5
        elif win_rate < 48:
            adjustment = -7
    return {
        "version": "V49_SELF_LEARNING_AI",
        "ok": True,
        "sample_signals": len(rows),
        "closed_trades": closed,
        "win_rate_pct": win_rate,
        "weight_adjustment": adjustment,
        "learning_state": "ACTIVE" if closed >= 30 else "WARMUP",
        "rule": "หลังมี closed trades >=30 ระบบเริ่มปรับน้ำหนักจากผลจริง",
    }


# V50 Portfolio Optimizer
def v50_portfolio_optimizer(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    symbols = symbols or DEFAULT_UNIVERSE[:8]
    rs = v44_relative_strength(symbols).get("items", [])
    macro = v47_macro_engine()
    risk_on = macro.get("macro_regime") == "RISK_ON"
    raw_scores = {}
    for item in rs:
        sym = item["symbol"]
        vol = _volatility_pct(_market_snapshot(sym, "3mo", "1d").get("closes", []), 20)
        rs_score = item.get("rs_score", 50)
        risk_penalty = max(0, vol - 40) * 0.6
        raw = max(1, rs_score - risk_penalty)
        if not risk_on and sym not in {"SPY", "QQQ"}:
            raw *= 0.75
        raw_scores[sym] = raw
    total = sum(raw_scores.values()) or 1
    max_weight = _safe_float(os.getenv("V50_MAX_WEIGHT_PCT", "30"), 30) or 30
    weights = []
    for sym, raw in raw_scores.items():
        w = min(max_weight, raw / total * 100)
        weights.append({"symbol": sym, "target_weight_pct": round(w, 2), "method": "RS + Volatility Target + Macro Filter"})
    # Renormalize after cap
    s = sum(w["target_weight_pct"] for w in weights) or 1
    for w in weights:
        w["target_weight_pct"] = round(w["target_weight_pct"] / s * 100, 2)
    weights.sort(key=lambda x: x["target_weight_pct"], reverse=True)
    return {
        "version": "V50_PORTFOLIO_OPTIMIZER",
        "ok": True,
        "macro_regime": macro.get("macro_regime"),
        "weights": weights,
        "constraints": {"max_weight_pct": max_weight},
        "rule": "Capital Allocation ด้วย Relative Strength + Volatility Targeting + Macro Filter",
    }


def build_v50_world_class_payload() -> Dict[str, Any]:
    portfolio = v43_portfolio_manager()
    rs = v44_relative_strength()
    options = v45_options_flow()
    dark = v46_dark_pool()
    macro = v47_macro_engine()
    mc = v48_monte_carlo()
    learning = v49_self_learning()
    optimizer = v50_portfolio_optimizer()
    return {
        "ok": True,
        "version": V50_VERSION,
        "time_th": _now_th(),
        "v43_portfolio_manager": portfolio,
        "v44_relative_strength": rs,
        "v45_options_flow": options,
        "v46_dark_pool": dark,
        "v47_macro_engine": macro,
        "v48_monte_carlo": mc,
        "v49_self_learning": learning,
        "v50_portfolio_optimizer": optimizer,
        "quality_rule": "World-class stack: portfolio-level risk before signal-level conviction",
    }


def build_v50_world_class_dashboard_text() -> str:
    p = build_v50_world_class_payload()
    port = p["v43_portfolio_manager"]
    macro = p["v47_macro_engine"]
    mc = p["v48_monte_carlo"]
    learn = p["v49_self_learning"]
    opt = p["v50_portfolio_optimizer"]
    rs_items = p["v44_relative_strength"].get("items", [])[:5]
    lines = [
        "🏛️ V50 WORLD-CLASS INSTITUTIONAL STACK",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        "V43 PORTFOLIO MANAGER",
        f"Heat: {port.get('portfolio_heat_pct')}% / Max {port.get('max_heat_pct')}% | Decision: {port.get('decision')}",
        f"Sector: {port.get('sector_exposure')}",
        "",
        "V44 RELATIVE STRENGTH TOP 5",
    ]
    for i, item in enumerate(rs_items, 1):
        lines.append(f"{i}. {item.get('symbol')} | RS {item.get('rs_score')} | {item.get('rank_bias')} | vs {item.get('benchmark')}")
    lines += [
        "",
        "V47 MACRO ENGINE",
        f"Regime: {macro.get('macro_regime')} | Risk Score: {macro.get('risk_score')}",
        "",
        "V48 MONTE CARLO",
        f"Expected Final R: {mc.get('expected_final_r')} | P95 MaxDD(R): {mc.get('p95_max_dd_r')} | Ruin Proxy: {mc.get('risk_of_ruin_proxy_pct')}%",
        "",
        "V49 SELF LEARNING",
        f"State: {learn.get('learning_state')} | Closed: {learn.get('closed_trades')} | Win: {learn.get('win_rate_pct')} | Adj: {learn.get('weight_adjustment')}",
        "",
        "V50 OPTIMIZER",
    ]
    for w in opt.get("weights", [])[:8]:
        lines.append(f"- {w.get('symbol')}: {w.get('target_weight_pct')}%")
    lines += ["", f"Version : {V50_VERSION}"]
    return "\n".join(lines)
