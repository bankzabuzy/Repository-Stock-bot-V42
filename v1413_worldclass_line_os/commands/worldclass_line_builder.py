from v1413_worldclass_line_os.api.priority_router import normalize_symbol, market_of, primary_source, reliability, time_th, session_of, api_health
from v1414_realtime_price_router.api.realtime_price_router import PriceRouter
from v1414_unified_status_control.commands.unified_status import VERSION, unified_control_center, symbol_api_status
from v1413_worldclass_line_os.core.market_brain import get_snapshot, expected_move, trade_plan, risk_sentence, entry_score, THAI_GOLD

_RT_ROUTER = PriceRouter()

def apply_realtime_quote(s):
    """Update snapshot object with freshest runtime price without crashing."""
    try:
        q = _RT_ROUTER.quote(s.symbol)
        if q:
            selected = q.get("selected_price")
            if selected:
                s.price = float(selected)
            if q.get("prev_close"):
                s.prev_close = float(q["prev_close"])
            if q.get("premarket") is not None:
                s.premarket = q.get("premarket")
            if q.get("regular") is not None:
                s.regular = q.get("regular")
            if q.get("afterhours") is not None:
                s.afterhours = q.get("afterhours")
            s._price_source = q.get("source", "UNKNOWN")
            s._price_mode = q.get("price_mode", "LATEST")
            s._price_timestamp = q.get("timestamp", time_th())
            s._price_stale = bool(q.get("stale", False))
            s._price_note = q.get("note", "")
            # gold extra fields
            for k in ["bar_buy","bar_sell","orn_buy","orn_sell","spread","xauusd","usdthb"]:
                if k in q:
                    setattr(s, "_" + k, q[k])
    except Exception as e:
        s._price_source = "PRICE_ROUTER_ERROR"
        s._price_mode = "FALLBACK"
        s._price_timestamp = time_th()
        s._price_stale = True
        s._price_note = str(e)
    return s

def quote_source_line(s, m):
    src = getattr(s, "_price_source", primary_source(m))
    mode = getattr(s, "_price_mode", "LATEST")
    ts = getattr(s, "_price_timestamp", time_th())
    stale = getattr(s, "_price_stale", False)
    note = getattr(s, "_price_note", "")
    warn = " ⚠️ ข้อมูลอาจล่าช้า" if stale else ""
    return f"Price: {mode} | Source: {src} | อัปเดต {ts}{warn}" + (f"\nหมายเหตุ: {note}" if note else "")


def money(v, market="US"):
    if v is None:
        return "N/A"
    if market == "TH" or market == "GOLD":
        return f"฿{v:,.2f}"
    return f"${v:,.2f}"

def pct_change(cur, prev):
    if cur is None or not prev:
        return "N/A"
    chg = cur - prev
    return f"{chg:+.2f} ({chg/prev*100:+.2f}%)"

def icon_for_view(view):
    view = (view or "").upper()
    if "BULL" in view:
        return "🟢"
    if "BEAR" in view:
        return "🔴"
    if "WAIT" in view:
        return "🟡"
    return "🟠"

def build_gold():
    g = THAI_GOLD
    s = apply_realtime_quote(get_snapshot("GOLD"))
    em = expected_move(s)
    plan = trade_plan(s)
    return f"""🏆 GOLD | ทองคำไทย
เวลา: {time_th()}
Source: สมาคมค้าทองคำ | {reliability('GOLD')}/100
{quote_source_line(s, 'GOLD')}

ราคาทองสมาคม:
รับซื้อทองแท่ง: {getattr(s, '_bar_buy', g['bar_buy']):,.0f}
ขายออกทองแท่ง: {getattr(s, '_bar_sell', g['bar_sell']):,.0f}
รับซื้อรูปพรรณ: {getattr(s, '_orn_buy', g['orn_buy']):,.0f}
ขายออกรูปพรรณ: {getattr(s, '_orn_sell', g['orn_sell']):,.0f}
Spread: {getattr(s, '_spread', g['spread']):,.0f} บาท

มุมมอง: 🟡 WAIT | Prob ขึ้น {s.prob_up}% | Conf {s.confidence}%
Risk: {s.risk_grade} | {risk_sentence(s)}

คาดการณ์ 1–3 วัน:
ขึ้น {em['up_prob']}% → {g['bar_sell']+300:,.0f}–{g['bar_sell']+700:,.0f}
ลง {em['down_prob']}% → {g['bar_sell']-300:,.0f}–{g['bar_sell']-600:,.0f}
สูงสุด/ต่ำสุดคาด: {g['bar_sell']+700:,.0f} / {g['bar_sell']-600:,.0f}

แผนทอง:
ไม้1 {g['bar_sell']-150:,.0f} | มั่นใจ 48%
ไม้2 {g['bar_sell']-300:,.0f} | มั่นใจ 42%
ไม้3 {g['bar_sell']-450:,.0f} | มั่นใจ 35%
TP {g['bar_sell']+300:,.0f}/{g['bar_sell']+500:,.0f}/{g['bar_sell']+700:,.0f}
SL {g['bar_sell']-600:,.0f}

ประกอบ: XAUUSD ${g['xauusd']:,.2f} | USDTHB {g['usdthb']}
เหตุผล: รอ DXY/Yield + London/NY ยืนยันก่อน
สรุปมือใหม่: ยังไม่ไล่ซื้อ รอใกล้แนวรับหรือสัญญาณกลับตัว

Version : {VERSION}"""

def build_stock(symbol):
    sym = normalize_symbol(symbol)
    s = apply_realtime_quote(get_snapshot(sym))
    m = market_of(sym)
    sess, note = session_of(m)
    em = expected_move(s)
    plan = trade_plan(s)
    source = primary_source(m)
    view_icon = icon_for_view(s.view)
    cur_line = f"ราคา: {money(s.price,m)} | เปลี่ยนแปลง {pct_change(s.price, s.prev_close)}"
    if m in {"US","ETF"}:
        price_line = f"Prev {money(s.prev_close,m)} | Pre {money(s.premarket,m)} | Regular {money(s.regular,m)} | After {money(s.afterhours,m)}"
    else:
        price_line = f"ล่าสุด {money(s.price,m)} | ปิดก่อนหน้า {money(s.prev_close,m)}"
    if plan["no_trade"]:
        plan_text = f"แผน 3 ไม้: NO TRADE\nเหตุผล: {plan['reason']}\nจุดเสี่ยงหลุด: {money(plan['sl'],m)}"
    else:
        e = plan["entries"]
        tp = plan["tp"]
        plan_text = (
            "แผน 3 ไม้:\n"
            f"1) {money(e[0][0],m)} | มั่นใจ {e[0][1]}% | เงิน {e[0][2]}%\n"
            f"2) {money(e[1][0],m)} | มั่นใจ {e[1][1]}% | เงิน {e[1][2]}%\n"
            f"3) {money(e[2][0],m)} | มั่นใจ {e[2][1]}% | เงิน {e[2][2]}%\n"
            f"TP {money(tp[0],m)} / {money(tp[1],m)} / {money(tp[2],m)}\n"
            f"SL {money(plan['sl'],m)}"
        )
    if m in {"US","ETF"}:
        call = s.price + s.atr14
        put = s.price - s.atr14
        opt_text = f"Options: CALL > {money(call,m)} | PUT < {money(put,m)} | DTE 7–21 วัน | Conf {max(30, s.confidence-7)}%"
    else:
        opt_text = "Options: ไม่มี / ไม่แนะนำสำหรับหุ้นไทยในระบบนี้"
    if s.rvol >= 1:
        vol_text = f"ซื้อ {s.buy_ratio}% / ขาย {s.sell_ratio}% | Volume ปกติถึงสูง"
    else:
        vol_text = f"ซื้อ {s.buy_ratio}% / ขาย {s.sell_ratio}% | Volume ยังเบา"

    return f"""{'🇹🇭' if m=='TH' else '🇺🇸'} {s.symbol} | {s.name}
เวลา: {time_th()}
Source: {source} | Session: {sess} | {reliability(m)}/100
{note}
{quote_source_line(s, m)}

{cur_line}
{price_line}

มุมมอง: {view_icon} {s.view}
AI Score {s.score}/100 | Prob ขึ้น {s.prob_up}% | Conf {s.confidence}%
Risk: {s.risk_grade} | {risk_sentence(s)}

คาดการณ์ 1–3 วัน:
ขึ้น {em['up_prob']}% → {money(em['high_3d'],m)}
ลง {em['down_prob']}% → {money(em['low_3d'],m)}
สูงสุด/ต่ำสุดวันนี้: {money(em['high_1d'],m)} / {money(em['low_1d'],m)}
Expected Move: ±{em['expected_pct']:.1f}%

Trend: 15m {s.trend_15m} | 1H {s.trend_1h} | 1D {s.trend_1d}
Technical: EMA6 {s.ema6:.2f} | EMA12 {s.ema12:.2f} | EMA50 {s.ema50:.2f} | RSI {s.rsi14:.2f}
พื้นฐาน: P/E {s.pe} | Fwd P/E {s.forward_pe} | Dividend {s.dividend_yield}% | ปันผลล่าสุด {s.dividend_last}

{plan_text}

{opt_text}
แรงซื้อขาย: {vol_text}

จังหวะเข้า: {entry_score(s)}/10
ข่าวสำคัญ:
1) {s.news1}
2) {s.news2}

ถ้ามีของ: ถือต่อได้ถ้าไม่หลุด SL
ถ้ายังไม่มี: รอ trigger อย่าไล่ราคา
สรุป: {s.key_reason}

Version : {VERSION}"""

def build_top5(kind="US"):
    k = (kind or "US").upper()
    universe = {
        "US": ["NVDA","QQQ","MSFT","TSM","AAPL"],
        "CALL": ["QQQ","MSFT","TSM","AAPL","NVDA"],
        "PUT": ["NVDA","TSLA","SOXL","IWM","QQQ"],
        "TH": ["SCB.BK","KBANK.BK","BBL.BK","PTT.BK","AOT.BK"],
        "ETF": ["QQQ","SPY","XLK","XLF","GLD"],
    }.get(k, ["NVDA","QQQ","SCB.BK","GOLD"])
    if k == "GOLD":
        return build_gold()
    lines = [f"🏆 Top5 {k} | มือใหม่อ่านง่าย", f"เวลา: {time_th()}", "กฎ: ไม่ไล่ราคา / รอ Trigger / คุม SL", ""]
    for i, sym in enumerate(universe, 1):
        s = apply_realtime_quote(get_snapshot(sym))
        m = market_of(sym)
        lines.append(f"{i}. {s.symbol} | {money(s.price,m)} | {s.view} | Prob {s.prob_up}% | Risk {s.risk_grade}")
        lines.append(f"   แผน: {'รอ' if s.prob_up<50 else 'รอเข้าใกล้ไม้1'} | เหตุผล: {s.key_reason[:42]}")
    lines.append("")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)

def dispatch(text):
    t = (text or "").strip()
    low = t.lower()
    compact = low.replace(" ","")
    if compact in {"api","status","สถานะ","สถานะระบบ","health","dashboard","control","ศูนย์ควบคุม"}:
        return unified_control_center()
    if low.startswith("api "):
        return symbol_api_status(t.split()[1])
    if compact in {"gold","ทอง","ทองคำ","top5gold"}:
        return build_gold()
    if compact in {"top5","top5us"}:
        return build_top5("US")
    if compact in {"top5call","call"}:
        return build_top5("CALL")
    if compact in {"top5put","put"}:
        return build_top5("PUT")
    if compact in {"top5th","topthai"}:
        return build_top5("TH")
    if compact in {"top5etf"}:
        return build_top5("ETF")
    if compact in {"help","คำสั่ง","v1413"}:
        return "คำสั่ง: nvda / qqq / scb / gold / top5 us / top5 th / top5 call / top5 put / api\n\nVersion : " + VERSION
    if t:
        return build_stock(t)
    return None
