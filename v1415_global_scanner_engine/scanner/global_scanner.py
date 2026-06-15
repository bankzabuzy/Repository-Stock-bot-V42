"""
global_scanner.py — V1416 LIVE DATA
เปลี่ยนจาก hardcode fallback → ดึงข้อมูล live ผ่าน market_brain ที่อัปเกรดแล้ว
scan_symbol() ตอนนี้ include: ราคา pre/post, change%, entry plan, live badge
"""
from v1415_global_scanner_engine.scanner.universe import get_universe, universe_size_text
from v1413_worldclass_line_os.core.market_brain import (
    get_snapshot, expected_move, trade_plan, entry_score, risk_sentence
)
from v1413_worldclass_line_os.api.priority_router import market_of, time_th

VERSION = "V1419_MASTER_CLEAN_FINAL"

# ─── formatters ───────────────────────────────────────────────
def money(v, market="US"):
    if v is None: return "N/A"
    try:
        if market in {"TH","GOLD"}: return f"฿{float(v):,.2f}"
        return f"${float(v):,.2f}"
    except Exception: return "N/A"

def _chg(pct):
    if pct is None: return ""
    try:
        arrow = "▲" if float(pct) >= 0 else "▼"
        return f" {arrow}{abs(float(pct)):.2f}%"
    except Exception: return ""

def _live_badge(snap) -> str:
    try:
        if snap.is_live: return f"🟢[Live·{snap.source[:10]}·{snap.data_ts}]"
        return f"🟡[Cached·{snap.data_ts}]" if snap.data_ts else "🔴[Fallback]"
    except Exception: return ""

def _risk_rank(risk):
    r = str(risk or "")
    if r.startswith("A"):  return 4
    if r.startswith("B+"): return 3.5
    if r.startswith("B"):  return 3
    if r.startswith("C+"): return 2
    if r.startswith("C"):  return 1
    return 0

# ─── scan_symbol ─────────────────────────────────────────────
def scan_symbol(symbol):
    s = get_snapshot(symbol)         # ← ตอนนี้ดึง live data จริง
    m = market_of(s.symbol)
    em = expected_move(s)
    plan = trade_plan(s)

    rank_score = (
        s.prob_up * 0.40 +
        s.confidence * 0.25 +
        entry_score(s) * 5 +
        _risk_rank(s.risk_grade) * 4 +
        (5 if s.rvol >= 1 else 0) +
        (5 if s.price > s.ema50 else 0)
    )

    if s.prob_up >= 55 and not str(s.view).upper().startswith("BEAR"):
        gate = "BUY_CANDIDATE"
    elif str(s.view).upper().startswith("BEAR") and s.prob_up < 50:
        gate = "SELL_OR_AVOID"
    elif s.prob_up >= 50:
        gate = "WATCH"
    else:
        gate = "NO_TRADE"

    entries = plan.get("entries", [])
    tps     = plan.get("tp", [])
    sl      = plan.get("sl")

    return {
        "symbol":      s.symbol,
        "market":      m,
        "price":       s.price,
        "change_pct":  getattr(s, "change_pct", None),
        "premarket":   s.premarket,
        "afterhours":  s.afterhours,
        "view":        s.view,
        "prob":        s.prob_up,
        "conf":        s.confidence,
        "risk":        s.risk_grade,
        "rsi":         s.rsi14,
        "rvol":        s.rvol,
        "entry_score": entry_score(s),
        "rank_score":  round(rank_score, 2),
        "gate":        gate,
        "reason":      s.key_reason,
        "news1":       s.news1,
        "high_3d":     em["high_3d"],
        "low_3d":      em["low_3d"],
        "entries":     entries,
        "tp":          tps,
        "sl":          sl,
        "no_trade":    plan.get("no_trade", False),
        "is_live":     getattr(s, "is_live", False),
        "source":      getattr(s, "source", ""),
        "data_ts":     getattr(s, "data_ts", ""),
        "_snap":       s,
    }

def scan_market(kind="GLOBAL", limit=5):
    rows = []
    for sym in get_universe(kind):
        try:
            rows.append(scan_symbol(sym))
        except Exception as e:
            print(f"[scanner] skip {sym}: {e}")
    buy   = sorted([r for r in rows if r["gate"] == "BUY_CANDIDATE"],  key=lambda r: r["rank_score"], reverse=True)
    watch = sorted([r for r in rows if r["gate"] == "WATCH"],          key=lambda r: r["rank_score"], reverse=True)
    avoid = sorted([r for r in rows if r["gate"] in {"NO_TRADE","SELL_OR_AVOID"}], key=lambda r: r["rank_score"])
    live_count = sum(1 for r in rows if r.get("is_live"))
    return {
        "buy": buy[:limit], "watch": watch[:limit], "avoid": avoid[:limit],
        "all_count": len(rows), "live_count": live_count,
    }

# ─── format_rows — เพิ่ม entry plan + pre/post + news ────────
def format_rows(title, rows, show_entry=True):
    if not rows:
        return title + "\n- ยังไม่มีตัวผ่านเกณฑ์"
    out = [title]
    for i, r in enumerate(rows, 1):
        m = r["market"]
        pre  = f"\n   ก่อนตลาด: {money(r['premarket'], m)}" if r.get("premarket") else ""
        post = f"\n   หลังตลาด: {money(r['afterhours'], m)}" if r.get("afterhours") else ""
        badge = f"{'🟢' if r.get('is_live') else '🔴'}"

        out.append(
            f"{i}. {badge} {r['symbol']} | {money(r['price'], m)}{_chg(r.get('change_pct'))}\n"
            f"   Prob {r['prob']}% | Conf {r['conf']}% | Risk {r['risk']} | RSI {r.get('rsi','N/A'):.0f} | Vol {r.get('rvol','N/A'):.1f}x{pre}{post}"
        )
        out.append(f"   เป้า 1–3 วัน: ▲{money(r['high_3d'], m)} / ▼{money(r['low_3d'], m)}")

        if show_entry and not r.get("no_trade") and r.get("entries"):
            e1, c1, p1 = r["entries"][0]
            tp_list = r.get("tp", [])
            sl_v    = r.get("sl")
            tp_str  = f"TP1 {money(tp_list[0], m)}" + (f" TP2 {money(tp_list[1], m)}" if len(tp_list) > 1 else "")
            out.append(f"   📍 Entry {money(e1, m)} (Conf {c1}%) | {tp_str} | SL {money(sl_v, m)}")

        reason = r.get("reason","")
        news   = r.get("news1","")
        if reason: out.append(f"   💡 {reason[:70]}")
        if news:   out.append(f"   📰 {news[:70]}")
    return "\n".join(out)

# ─── main message builder ────────────────────────────────────
def global_scan_message(kind="GLOBAL"):
    result = scan_market(kind, 5)
    live_info = f"Live: {result['live_count']}/{result['all_count']} ตัว"
    return (
        f"🌍 GLOBAL SCANNER {VERSION}\n"
        f"เวลา: {time_th()} | {live_info}\n"
        f"Universe: {universe_size_text()} | ตลาด: {kind.upper()}\n\n"
        f"{format_rows('✅ Top5 BUY / น่าสนใจ', result['buy'])}\n\n"
        f"{format_rows('🟡 WATCH / รอจังหวะ', result['watch'], show_entry=False)}\n\n"
        f"{format_rows('⛔ AVOID / ยังไม่เข้า', result['avoid'], show_entry=False)}\n\n"
        f"กฎระบบ:\n"
        f"🟢 = ข้อมูล Live | 🔴 = ข้อมูลสำรอง\n"
        f"- BUY: Prob ≥ 55 + ไม่ Bearish\n"
        f"- WATCH: Prob ≥ 50 แต่ยังไม่ครบเงื่อนไข\n"
        f"- Entry ราคา ± 0.5% | SL ห้ามฝืน\n\n"
        f"Version : {VERSION}"
    )
