
# V51 INSTITUTIONAL VALIDATION AND EXECUTION PROOF
# Real Backtest + Walk Forward + Paper Broker + Data Quality Guard
# Kill Switch + Calibration Curve + Slippage/Commission + Live Execution Journal
# Portfolio Exposure
# Fail-safe: no function should crash the worker.

from __future__ import annotations

import os
import math
import random
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

try:
    import yfinance as yf  # type: ignore
except Exception:
    yf = None

V51_VERSION = "V51_INSTITUTIONAL_VALIDATION_AND_EXECUTION_PROOF_STABLE"
DEFAULT_SYMBOLS = ["NVDA", "AAPL", "TSLA", "QQQ", "SPY", "TSM", "AMD", "MSFT"]


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


def _db_path() -> str:
    return os.getenv("DB_PATH", "signals.db")


def _yf_closes(symbol: str, period: str = "2y", interval: str = "1d") -> Dict[str, Any]:
    if yf is None:
        return {"ok": False, "symbol": symbol, "closes": [], "reason": "yfinance_not_available"}
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True, threads=False)
        if df is None or df.empty:
            return {"ok": False, "symbol": symbol, "closes": [], "reason": "no_data"}
        closes = [float(x) for x in df["Close"].dropna().values]
        return {"ok": bool(closes), "symbol": symbol, "closes": closes, "last": closes[-1] if closes else None, "source": "Yahoo Finance"}
    except Exception as e:
        return {"ok": False, "symbol": symbol, "closes": [], "reason": str(e)}


def v51_init_db() -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(_db_path())
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v51_execution_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT,
                status TEXT,
                entry REAL,
                qty REAL,
                tp REAL,
                sl REAL,
                exit_price REAL,
                pnl REAL,
                pnl_pct REAL,
                probability REAL,
                confidence REAL,
                source_version TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v51_kill_switch_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v51_portfolio_positions (
                symbol TEXT PRIMARY KEY,
                qty REAL,
                avg_price REAL,
                last_price REAL,
                market_value REAL,
                unrealized_pnl REAL,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()
        return {"ok": True, "db": _db_path()}
    except Exception as e:
        return {"ok": False, "db": _db_path(), "error": str(e)}


def data_quality_guard(symbol: str) -> Dict[str, Any]:
    snap = _yf_closes(symbol, "5d", "1d")
    closes = snap.get("closes", [])
    issues = []
    if not snap.get("ok"):
        issues.append(snap.get("reason", "no_data"))
    if len(closes) < 2:
        issues.append("insufficient_price_history")
    if closes and closes[-1] <= 0:
        issues.append("invalid_last_price")
    if len(closes) >= 2 and closes[-2] != 0:
        jump = abs((closes[-1] - closes[-2]) / closes[-2] * 100)
        if jump > float(os.getenv("V51_MAX_DAILY_PRICE_JUMP_PCT", "25")):
            issues.append(f"abnormal_price_jump_{round(jump,2)}pct")
    return {
        "ok": len(issues) == 0,
        "symbol": symbol,
        "issues": issues,
        "last_price": closes[-1] if closes else None,
        "rule": "ถ้าข้อมูลราคาไม่ดี ห้ามใช้สัญญาณ",
    }


def _ema(values: List[float], n: int) -> List[float]:
    if not values:
        return []
    k = 2 / (n + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def _strategy_signal(closes: List[float], idx: int) -> str:
    if idx < 60:
        return "WAIT"
    sub = closes[:idx+1]
    e12 = _ema(sub, 12)[-1]
    e50 = _ema(sub, 50)[-1]
    if e12 > e50 and closes[idx] > e12:
        return "BUY"
    if e12 < e50 and closes[idx] < e12:
        return "SELL"
    return "WAIT"


def real_backtest(symbol: str = "SPY", period: str = "3y", commission_pct: float = 0.05, slippage_pct: float = 0.08) -> Dict[str, Any]:
    snap = _yf_closes(symbol, period, "1d")
    closes = snap.get("closes", [])
    if len(closes) < 120:
        return {"ok": False, "symbol": symbol, "reason": "insufficient_data", "source": snap}
    trades = []
    pos = None
    entry = 0.0
    for i in range(60, len(closes)-1):
        sig = _strategy_signal(closes, i)
        px = closes[i+1] * (1 + slippage_pct/100)
        if pos is None and sig == "BUY":
            pos = "LONG"
            entry = px
        elif pos == "LONG" and sig in {"SELL", "WAIT"}:
            exit_px = closes[i+1] * (1 - slippage_pct/100)
            pnl_pct = (exit_px - entry) / entry * 100 - commission_pct * 2
            trades.append(pnl_pct)
            pos = None
    if pos == "LONG":
        exit_px = closes[-1] * (1 - slippage_pct/100)
        trades.append((exit_px - entry) / entry * 100 - commission_pct * 2)
    wins = [x for x in trades if x > 0]
    losses = [abs(x) for x in trades if x < 0]
    equity = 0
    peak = 0
    max_dd = 0
    for t in trades:
        equity += t
        peak = max(peak, equity)
        max_dd = max(max_dd, peak-equity)
    return {
        "ok": True,
        "version": "V51_REAL_BACKTEST",
        "symbol": symbol,
        "period": period,
        "trades": len(trades),
        "win_rate_pct": round(len(wins)/len(trades)*100,2) if trades else None,
        "profit_factor": round(sum(wins)/sum(losses),2) if losses else None,
        "total_return_pct_proxy": round(sum(trades),2),
        "max_drawdown_pct_proxy": round(max_dd,2),
        "expectancy_pct": round(sum(trades)/len(trades),2) if trades else None,
        "commission_pct": commission_pct,
        "slippage_pct": slippage_pct,
    }


def walk_forward(symbol: str = "SPY") -> Dict[str, Any]:
    snap = _yf_closes(symbol, "5y", "1d")
    closes = snap.get("closes", [])
    if len(closes) < 500:
        return {"ok": False, "symbol": symbol, "reason": "insufficient_data"}
    windows = []
    size = max(120, len(closes)//8)
    for start in range(0, len(closes)-size, size//2):
        part = closes[start:start+size]
        if len(part) < 120:
            continue
        # Use local copy via same logic by injecting simple backtest loop.
        trades = []
        pos = None
        entry = 0
        for i in range(60, len(part)-1):
            sig = _strategy_signal(part, i)
            if pos is None and sig == "BUY":
                pos = "LONG"; entry = part[i+1]
            elif pos == "LONG" and sig in {"SELL", "WAIT"}:
                trades.append((part[i+1]-entry)/entry*100)
                pos = None
        wins = [x for x in trades if x > 0]
        losses = [abs(x) for x in trades if x < 0]
        windows.append({
            "window": len(windows)+1,
            "trades": len(trades),
            "win_rate_pct": round(len(wins)/len(trades)*100,2) if trades else None,
            "profit_factor": round(sum(wins)/sum(losses),2) if losses else None,
            "return_pct_proxy": round(sum(trades),2),
        })
    valid = [w for w in windows if w.get("trades")]
    return {
        "ok": True,
        "version": "V51_WALK_FORWARD",
        "symbol": symbol,
        "windows": windows,
        "passed_windows": sum(1 for w in valid if (w.get("profit_factor") or 0) >= 1.2 and (w.get("win_rate_pct") or 0) >= 50),
        "total_windows": len(valid),
        "rule": "ดูว่ากลยุทธ์ยังมี edge หลายช่วงตลาดหรือไม่",
    }


def paper_broker_order(symbol: str, side: str = "BUY", qty: float = 1.0, entry: Optional[float] = None, tp: Optional[float] = None, sl: Optional[float] = None, probability: Any = None, confidence: Any = None) -> Dict[str, Any]:
    v51_init_db()
    dq = data_quality_guard(symbol)
    if not dq.get("ok"):
        return {"ok": False, "reason": "data_quality_failed", "data_quality": dq}
    price = _safe_float(entry, dq.get("last_price")) or dq.get("last_price")
    side = side.upper()
    try:
        conn = sqlite3.connect(_db_path())
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO v51_execution_journal(created_at,symbol,side,status,entry,qty,tp,sl,probability,confidence,source_version)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (datetime.now(timezone.utc).isoformat(), symbol.upper(), side, "OPEN", price, qty, tp, sl, _safe_float(probability), _safe_float(confidence), V51_VERSION))
        oid = cur.lastrowid
        conn.commit(); conn.close()
        return {"ok": True, "order_id": oid, "symbol": symbol.upper(), "side": side, "entry": price, "qty": qty, "tp": tp, "sl": sl}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def update_paper_broker(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    v51_init_db()
    updated = []
    try:
        conn = sqlite3.connect(_db_path())
        cur = conn.cursor()
        cur.execute("SELECT id,symbol,side,entry,qty,tp,sl FROM v51_execution_journal WHERE status='OPEN'")
        rows = cur.fetchall()
        for oid, sym, side, entry, qty, tp, sl in rows:
            if symbols and sym not in symbols:
                continue
            dq = data_quality_guard(sym)
            px = _safe_float(dq.get("last_price"))
            if px is None:
                continue
            outcome = None
            if side == "BUY":
                if tp is not None and px >= tp: outcome = "TP"
                elif sl is not None and px <= sl: outcome = "SL"
                pnl = (px - entry) * qty
                pnl_pct = (px-entry)/entry*100 if entry else None
            else:
                if tp is not None and px <= tp: outcome = "TP"
                elif sl is not None and px >= sl: outcome = "SL"
                pnl = (entry - px) * qty
                pnl_pct = (entry-px)/entry*100 if entry else None
            if outcome:
                cur.execute("UPDATE v51_execution_journal SET status='CLOSED', outcome=?, exit_price=?, pnl=?, pnl_pct=? WHERE id=?", (outcome, px, pnl, pnl_pct, oid))
                updated.append({"id": oid, "symbol": sym, "outcome": outcome, "exit_price": px, "pnl": round(pnl,2), "pnl_pct": round(pnl_pct or 0,2)})
        conn.commit(); conn.close()
        return {"ok": True, "updated": updated}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def kill_switch() -> Dict[str, Any]:
    v51_init_db()
    max_daily_loss = float(os.getenv("V51_MAX_DAILY_LOSS_PCT", "2"))
    max_losing_streak = int(os.getenv("V51_MAX_LOSING_STREAK", "3"))
    try:
        conn = sqlite3.connect(_db_path())
        cur = conn.cursor()
        cur.execute("SELECT pnl_pct FROM v51_execution_journal WHERE status='CLOSED' ORDER BY id DESC LIMIT 20")
        rows = [r[0] for r in cur.fetchall() if r[0] is not None]
        conn.close()
        losing_streak = 0
        for x in rows:
            if x < 0: losing_streak += 1
            else: break
        daily_loss = abs(sum(x for x in rows[:10] if x < 0))
        active = losing_streak >= max_losing_streak or daily_loss >= max_daily_loss
        return {"ok": True, "active": active, "losing_streak": losing_streak, "daily_loss_proxy_pct": round(daily_loss,2), "rule": "หยุดระบบเมื่อแพ้ติดกันหรือขาดทุนเกิน limit"}
    except Exception as e:
        return {"ok": False, "active": False, "error": str(e)}


def calibration_curve() -> Dict[str, Any]:
    v51_init_db()
    buckets = {50: [], 60: [], 70: [], 80: [], 90: []}
    try:
        conn = sqlite3.connect(_db_path())
        cur = conn.cursor()
        cur.execute("SELECT probability,pnl FROM v51_execution_journal WHERE status='CLOSED' AND probability IS NOT NULL")
        rows = cur.fetchall(); conn.close()
        for prob, pnl in rows:
            p = float(prob)
            key = max(k for k in buckets if p >= k) if p >= 50 else 50
            buckets[key].append(1 if (pnl or 0) > 0 else 0)
        result = []
        for k, vals in buckets.items():
            result.append({"bucket": f"{k}+", "count": len(vals), "realized_win_rate_pct": round(sum(vals)/len(vals)*100,2) if vals else None})
        return {"ok": True, "version": "V51_CALIBRATION_CURVE", "buckets": result, "rule": "เทียบ Probability ที่ระบบบอกกับผลชนะจริง"}
    except Exception as e:
        return {"ok": False, "error": str(e), "buckets": []}


def portfolio_exposure() -> Dict[str, Any]:
    v51_init_db()
    try:
        conn = sqlite3.connect(_db_path())
        cur = conn.cursor()
        cur.execute("SELECT symbol,qty,avg_price,last_price,market_value,unrealized_pnl FROM v51_portfolio_positions")
        rows = cur.fetchall(); conn.close()
        items = [{"symbol": r[0], "qty": r[1], "avg_price": r[2], "last_price": r[3], "market_value": r[4], "unrealized_pnl": r[5]} for r in rows]
    except Exception:
        # env fallback
        raw = os.getenv("V50_POSITIONS", "NVDA:8,TSM:6,QQQ:12,THAI_GOLD:10")
        items = [{"symbol": p.split(":")[0].strip().upper(), "weight_pct": _safe_float(p.split(":")[1],0) if ":" in p else 0} for p in raw.split(",") if p.strip()]
    total = sum(_safe_float(i.get("market_value"), _safe_float(i.get("weight_pct"), 0)) or 0 for i in items)
    return {"ok": True, "version": "V51_PORTFOLIO_EXPOSURE", "items": items, "total_exposure_proxy": round(total,2)}


def build_v51_payload(symbol: str = "SPY") -> Dict[str, Any]:
    dq = data_quality_guard(symbol)
    bt = real_backtest(symbol)
    wf = walk_forward(symbol)
    upd = update_paper_broker()
    ks = kill_switch()
    cal = calibration_curve()
    exp = portfolio_exposure()
    return {
        "ok": True,
        "version": V51_VERSION,
        "time_th": _now_th(),
        "symbol": symbol,
        "data_quality_guard": dq,
        "real_backtest": bt,
        "walk_forward": wf,
        "paper_broker_update": upd,
        "kill_switch": ks,
        "calibration_curve": cal,
        "portfolio_exposure": exp,
        "quality_rule": "V51 proves execution and edge before scaling capital",
    }


def build_v51_dashboard_text(symbol: str = "SPY") -> str:
    p = build_v51_payload(symbol)
    bt = p.get("real_backtest", {})
    wf = p.get("walk_forward", {})
    ks = p.get("kill_switch", {})
    dq = p.get("data_quality_guard", {})
    exp = p.get("portfolio_exposure", {})
    lines = [
        "🧪 V51 INSTITUTIONAL VALIDATION & EXECUTION PROOF",
        f"เวลาไทย: {p.get('time_th')}",
        f"Symbol: {symbol}",
        "",
        f"Data Quality: {'✅' if dq.get('ok') else '❌'} | Issues: {dq.get('issues')}",
        f"Kill Switch: {'🔴 ACTIVE' if ks.get('active') else '🟢 OK'} | Losing Streak: {ks.get('losing_streak')}",
        "",
        "REAL BACKTEST",
        f"Trades: {bt.get('trades')} | Win: {bt.get('win_rate_pct')} | PF: {bt.get('profit_factor')} | DD: {bt.get('max_drawdown_pct_proxy')} | Exp: {bt.get('expectancy_pct')}",
        "",
        "WALK FORWARD",
        f"Passed: {wf.get('passed_windows')}/{wf.get('total_windows')}",
        "",
        "CALIBRATION",
    ]
    for b in (p.get("calibration_curve", {}).get("buckets") or []):
        lines.append(f"- {b.get('bucket')}: count {b.get('count')} | realized {b.get('realized_win_rate_pct')}")
    lines += [
        "",
        "PORTFOLIO EXPOSURE",
        f"Total Exposure Proxy: {exp.get('total_exposure_proxy')}",
        "",
        f"Version : {V51_VERSION}",
    ]
    return "\n".join(lines)
