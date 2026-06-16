
from v1413_worldclass_line_os.api.priority_router import (
    normalize_symbol, market_of, primary_source, reliability, time_th, session_of, api_health
)
from v1414_realtime_price_router.api.realtime_price_router import PriceRouter
from v1414_unified_status_control.commands.unified_status import unified_control_center, symbol_api_status
from v1415_global_scanner_engine.scanner.global_scanner import global_scan_message
from v1413_worldclass_line_os.core.market_brain import (
    get_snapshot, expected_move, trade_plan, risk_sentence, entry_score, THAI_GOLD
)
import os, time, math, requests, datetime, threading

VERSION = "V1419_MASTER_CLEAN_FINAL"
_RT_ROUTER = PriceRouter()
_FG_CACHE = {"val": None, "ts": 0}
_FG_LOCK = threading.Lock()

# ─── Universes ────────────────────────────────────────────────
US_UNIVERSE   = ["NVDA","MSFT","AAPL","TSM","META","GOOGL","AMZN","JPM","ORCL","CRM",
                 "AMD","TSLA","NFLX","COIN","PLTR","ARM","AVGO","QCOM","MU","SMCI"]
TH_UNIVERSE   = ["SCB.BK","KBANK.BK","BBL.BK","PTT.BK","AOT.BK","ADVANC.BK","CPALL.BK",
                 "PTTEP.BK","BDMS.BK","DELTA.BK","KTC.BK","GULF.BK","MINT.BK","TRUE.BK","MAJOR.BK"]
CALL_UNIVERSE = ["QQQ","MSFT","TSM","AAPL","NVDA","META","GOOGL","SPY","AMZN","ORCL",
                 "ARM","AVGO","AMD","SMCI","CRM"]
PUT_UNIVERSE  = ["NVDA","TSLA","SOXL","IWM","QQQ","TQQQ","ARKK","PLTR","COIN","MSTR",
                 "SMCI","MU","AMD","NFLX","RIVN"]
ETF_UNIVERSE  = ["QQQ","SPY","XLK","XLF","GLD","XLE","XLV","IWM","EEM","SOXX",
                 "ARKK","SOXL","TLT","VNQ","DIA"]
PRE_UNIVERSE  = ["NVDA","AAPL","MSFT","TSLA","META","GOOGL","AMZN","AMD","SPY","QQQ",
                 "SMCI","COIN","PLTR","ARM","MU"]
GLOBAL_UNI    = US_UNIVERSE[:8] + TH_UNIVERSE[:4] + ["GOLD"]

# ─── Price router ─────────────────────────────────────────────
def _apply_rt(s):
    try:
        q = _RT_ROUTER.quote(s.symbol)
        if not q:
            return s
        for attr, key in [("price","selected_price"),("prev_close","prev_close"),
                          ("premarket","premarket"),("regular","regular"),("afterhours","afterhours")]:
            v = q.get(key)
            if v is not None:
                try:
                    setattr(s, attr, float(v))
                except Exception:
                    pass
        s._src   = q.get("source","?")
        s._mode  = q.get("price_mode","?")
        s._ts    = q.get("timestamp", time_th())
        s._stale = bool(q.get("stale", False))
        s._age   = q.get("age_seconds")
        s._note  = q.get("note","")
        for k in ["bar_buy","bar_sell","orn_buy","orn_sell","spread","xauusd","usdthb"]:
            if k in q:
                setattr(s,"_"+k, q[k])
    except Exception as e:
        s._src = "RT_ERROR"; s._stale = True; s._note = str(e)
    return s

def _live_line(s):
    live = getattr(s,"is_live",False)
    stale = getattr(s,"_stale",False)
    src = getattr(s,"_src","?")
    ts = getattr(s,"_ts",time_th())
    if live and not stale:  return f"🟢 Live · {src} · {ts}"
    if live and stale:      return f"🟡 Live(ล่าช้า) · {src} · {ts}"
    return f"🔴 Fallback · {ts}"

# ─── Formatters ───────────────────────────────────────────────
def _m(v, mk="US"):
    if v is None: return "N/A"
    try:
        return f"฿{float(v):,.2f}" if mk in ("TH","GOLD") else f"${float(v):,.2f}"
    except Exception: return "N/A"

def _chg(cur, prev):
    if not cur or not prev: return ""
    try:
        d = cur - prev
        a = "▲" if d >= 0 else "▼"
        return f" {a}{abs(d):.2f} ({d/prev*100:+.2f}%)"
    except Exception: return ""

def _bar(score, w=12):
    score = max(0,min(100,int(score or 0)))
    f = int(score/100*w)
    return "█"*f + "░"*(w-f)

def _grade_emoji(g):
    g = str(g or "")
    if g.startswith("A"):  return "🏆"
    if g.startswith("B+"): return "✅"
    if g.startswith("B"):  return "👍"
    if g.startswith("C"):  return "⚠️"
    return "❌"

def _signal_emoji(view):
    v = str(view or "").upper()
    if "BULL" in v: return "🟢"
    if "BEAR" in v: return "🔴"
    if "WAIT" in v: return "🟡"
    return "🟠"

# ─── Session timing ───────────────────────────────────────────
def _session_info():
    try:
        import pytz
        now_et = datetime.datetime.now(pytz.timezone("US/Eastern"))
        h, mn = now_et.hour, now_et.minute
        t = h*60+mn
        if 240<=t<570:
            return "🟡 US ก่อนเปิดตลาด (4:00–9:30 ET)", "เวลาเตรียมตัว — ดู pre-market, ไม่ควร all-in"
        elif 570<=t<630:
            return "⚡ US ช่วงเปิดตลาด Golden Hour (9:30–10:30 ET)", "จังหวะดีที่สุด — สัญญาณแรกของวันชัดสุด"
        elif 630<=t<780:
            return "😴 US ช่วงเงียบ Lunch (10:30–13:00 ET)", "Volume เบา — รอ PM session ดีกว่าไล่ราคา"
        elif 780<=t<900:
            return "🟢 US Afternoon Session (13:00–15:00 ET)", "ตลาดเริ่มกลับมา — สังเกต trend continuation"
        elif 900<=t<960:
            return "⚡ US Power Hour (15:00–16:00 ET)", "จังหวะดีรองลงมา — สัญญาณปิดวันสำคัญ"
        elif 960<=t<1200:
            return "🟠 US After-Hours (16:00–20:00 ET)", "ระวัง spread กว้าง — ดูข่าว earnings หลังปิด"
        else:
            return "⚫ US ตลาดปิด", "เวลาวิเคราะห์และเตรียมแผนพรุ่งนี้"
    except Exception:
        return "ตลาด: ไม่ทราบ session", ""

# ─── Fear & Greed (cached 10 min) ────────────────────────────
def _get_fg():
    with _FG_LOCK:
        if _FG_CACHE["val"] is not None and time.time() - _FG_CACHE["ts"] < 600:
            return _FG_CACHE["val"], _FG_CACHE.get("txt","N/A")
    try:
        r = requests.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            headers={"User-Agent":"Mozilla/5.0"}, timeout=5)
        d = r.json()
        val = int(float(d.get("fear_and_greed",{}).get("score",50)))
        txt = d.get("fear_and_greed",{}).get("rating","N/A")
        with _FG_LOCK:
            _FG_CACHE.update({"val":val,"txt":txt,"ts":time.time()})
        return val, txt
    except Exception:
        return None, "N/A"

def _fg_advice(val):
    if val is None:   return "ไม่มีข้อมูล"
    if val<=20:       return "🔴 กลัวมากสุด — โอกาสซื้อสะสม Warren Buffett style"
    if val<=40:       return "🟠 กลัว — ตลาดระวัง รอจังหวะย่อซื้อ"
    if val<=60:       return "⚪ เป็นกลาง — รอ signal ชัดก่อน"
    if val<=80:       return "🟡 โลภ — ระวัง overextended ลด sizing"
    return             "🔴 โลภสุด — ใกล้ top เสี่ยงสูง ไม่ควรไล่ราคา"

# ─── Sector rotation (simple heuristic) ───────────────────────
_SECTOR_MAP = {
    "Tech":    ["NVDA","MSFT","AAPL","META","GOOGL","AMD","AVGO","QCOM"],
    "Finance": ["JPM","GS","BAC","WFC","C","MS"],
    "Energy":  ["XOM","CVX","COP","SLB","PSX"],
    "Health":  ["JNJ","UNH","PFE","ABBV","MRK"],
    "Defense": ["LMT","RTX","NOC","GD","BA"],
}
def _sector_signal():
    lines = []
    for sector, syms in _SECTOR_MAP.items():
        try:
            up = 0
            for sym in syms[:4]:  # check top 4 per sector
                try:
                    s = get_snapshot(sym)
                    if s.price and s.prev_close and s.price > s.prev_close:
                        up += 1
                except Exception:
                    pass
            pct = up / min(len(syms), 4) * 100
            arrow = "▲" if pct >= 60 else ("▼" if pct <= 40 else "→")
            lines.append(f"{sector}: {arrow} {pct:.0f}% ขึ้น")
        except Exception:
            pass
    return "\n".join(lines) if lines else "ไม่มีข้อมูล"

# ─── Beginner glossary ────────────────────────────────────────
_GLOSSARY = {
    "rsi": "RSI = ดัชนีวัดแรงซื้อ-ขาย | < 30 = ถูกเกิน(โอกาสซื้อ) | > 70 = แพงเกิน(ระวัง)",
    "ema": "EMA = เส้นค่าเฉลี่ยราคา | ราคา > EMA = Uptrend | ราคา < EMA = Downtrend",
    "atr": "ATR = ช่วงราคาเฉลี่ยต่อวัน | ใช้คำนวณ SL และ TP",
    "rvol": "RVOL = ปริมาณซื้อขายเทียบค่าเฉลี่ย | > 1.2x = Volume สูงผิดปกติ = สัญญาณแรง",
    "sl":  "SL (Stop Loss) = จุดตัดขาดทุน | ห้ามฝืน — ตัด SL เสมอ",
    "tp":  "TP (Take Profit) = เป้าหมายกำไร | TP1 = แรก TP2 = กลาง TP3 = เต็ม",
    "kelly": "Kelly Criterion = สูตรคำนวณขนาดไม้ที่เหมาะสม ไม่ over-bet",
    "prob": "Prob = ความน่าจะเป็นขึ้น/ลง คำนวณจาก AI Score + Technical",
    "conf": "Confidence = ความมั่นใจของสัญญาณ ยิ่งสูงยิ่งชัด",
}

# ─── Kelly ────────────────────────────────────────────────────
def build_kelly(wr=0.55, aw=1.5, al=1.0, cap=100000):
    try:
        p=float(wr); b=float(aw)/float(al); q=1-p
        k=max(0,(p*b-q)/b); hk=k/2
        return (
            f"📐 Kelly Criterion — ขนาดไม้ที่เหมาะสม\n"
            f"สมมติ: Win Rate {wr*100:.0f}% | Avg Win {aw}R | Avg Loss {al}R\n\n"
            f"Kelly เต็ม: {k*100:.1f}% = ฿{cap*k:,.0f}\n"
            f"Half-Kelly (แนะนำ): {hk*100:.1f}% = ฿{cap*hk:,.0f}\n\n"
            f"คำอธิบายมือใหม่:\n"
            f"• Kelly เต็ม = risk สูงสุดตามคณิตศาสตร์\n"
            f"• Half-Kelly = ปลอดภัยกว่า ลด Drawdown ~50%\n"
            f"• ตัวอย่าง: ทุน 100,000 → ใส่ไม้ละ {cap*hk:,.0f} บาทสูงสุด\n\n"
            f"Version : {VERSION}"
        )
    except Exception:
        return "Kelly error\n\nVersion : " + VERSION

# ─── Market overview (beginner-friendly) ──────────────────────
def build_market():
    sess, timing = _session_info()
    fg_val, fg_txt = _get_fg()
    fg_bar = _bar(fg_val or 50)
    fg_adv = _fg_advice(fg_val)
    fg_str = f"{fg_val}/100 ({fg_txt})" if fg_val else "N/A"
    return (
        f"🌍 ภาพรวมตลาด | {time_th()}\n"
        f"═══════════════════\n"
        f"เซสชั่น: {sess}\n"
        f"💡 {timing}\n\n"
        f"😨 Fear & Greed: {fg_str}\n"
        f"[{fg_bar}]\n"
        f"{fg_adv}\n\n"
        f"🏭 Sector Rotation:\n{_sector_signal()}\n\n"
        f"📚 มือใหม่ควรรู้:\n"
        f"• F&G < 25 = ทุกคนกลัว → นักลงทุนมือโปรซื้อสะสม\n"
        f"• F&G > 75 = ทุกคนโลภ → ใกล้จุดพัก/จุดกลับตัว\n"
        f"• ซื้อตาม Sector ที่เงินกำลังไหลเข้า\n"
        f"• อย่าไล่ราคาตอน F&G > 75 + ราคาขึ้นเร็ว\n\n"
        f"Version : {VERSION}"
    )

# ─── Gold (beginner-friendly) ────────────────────────────────
def build_gold():
    g = THAI_GOLD
    s = _apply_rt(get_snapshot("GOLD"))
    em = expected_move(s)
    plan = trade_plan(s)
    bs = getattr(s,"_bar_sell",g["bar_sell"])
    bb = getattr(s,"_bar_buy",g["bar_buy"])
    os_ = getattr(s,"_orn_sell",g["orn_sell"])
    ob_ = getattr(s,"_orn_buy",g["orn_buy"])
    sp_ = getattr(s,"_spread",g["spread"])
    xu  = getattr(s,"_xauusd",g["xauusd"])
    ub  = getattr(s,"_usdthb",g["usdthb"])

    if plan["no_trade"]:
        pt = f"สถานะ: NO TRADE\nเหตุผล: {plan.get('reason','')}\nSL: {bs-600:,.0f}"
    else:
        tp = plan["tp"]
        pt = (f"แผน 3 ไม้:\nไม้1 ฿{bs-150:,.0f} | ไม้2 ฿{bs-300:,.0f} | ไม้3 ฿{bs-450:,.0f}\n"
              f"TP: ฿{tp[0]:,.0f} / ฿{tp[1]:,.0f} / ฿{tp[2]:,.0f}\nSL: ฿{bs-600:,.0f}")

    return (
        f"🏆 GOLD | ทองคำไทย\n{time_th()}\n{_live_line(s)}\n"
        f"═══════════════════\n"
        f"ราคาสมาคมค้าทองคำ:\n"
        f"ขายออกทองแท่ง: ฿{bs:,.0f}\n"
        f"รับซื้อทองแท่ง: ฿{bb:,.0f}\n"
        f"ขายออกรูปพรรณ: ฿{os_:,.0f}\n"
        f"รับซื้อรูปพรรณ: ฿{ob_:,.0f}\n"
        f"Spread: ฿{sp_:,.0f} | XAUUSD: ${xu:,.2f} | USD/THB: {ub}\n\n"
        f"มุมมอง: {_signal_emoji(s.view)} {s.view}\n"
        f"Score: {s.score}/100 [{_bar(s.score)}]\n"
        f"Prob ขึ้น: {s.prob_up}% | Risk: {s.risk_grade} {_grade_emoji(s.risk_grade)}\n"
        f"คาดการณ์ 3 วัน: ▲฿{em['high_3d']:,.0f} / ▼฿{em['low_3d']:,.0f}\n\n"
        f"{pt}\n\n"
        f"📚 มือใหม่:\n"
        f"• ทองแท่ง: Spread น้อยกว่า เหมาะเทรด\n"
        f"• รูปพรรณ: Spread ฿{sp_:,.0f} เหมาะสะสมระยะยาว\n"
        f"• ทองไทยตาม XAUUSD (USD) × USD/THB\n"
        f"• Dollar ขึ้น → ทองมักลง / Dollar ลง → ทองมักขึ้น\n\n"
        f"Version : {VERSION}"
    )

# ─── Single stock (full, beginner-friendly) ──────────────────
def build_stock(symbol):
    sym = normalize_symbol(symbol)
    s = _apply_rt(get_snapshot(sym))
    m = market_of(sym)
    sess, sess_note = _session_info()
    em = expected_move(s)
    plan = trade_plan(s)
    vi = _signal_emoji(s.view)
    ge = _grade_emoji(s.risk_grade)

    if m in ("US","ETF"):
        price_block = (
            f"ราคา: {_m(s.price,m)}{_chg(s.price,s.prev_close)}\n"
            f"Prev: {_m(s.prev_close,m)} | Pre: {_m(s.premarket,m)} | After: {_m(s.afterhours,m)}"
        )
    else:
        price_block = f"ราคา: {_m(s.price,m)}{_chg(s.price,s.prev_close)}\nปิดก่อนหน้า: {_m(s.prev_close,m)}"

    if plan["no_trade"]:
        plan_block = f"แผนเทรด: NO TRADE ⛔\nเหตุผล: {plan.get('reason','')}\nSL: {_m(plan.get('sl'),m)}"
    else:
        e=plan["entries"]; tp=plan["tp"]; sl=plan["sl"]
        plan_block = (
            f"แผน 3 ไม้ (แบ่งเงินเท่ากัน 3 ครั้ง):\n"
            f"ไม้1 {_m(e[0][0],m)} | มั่นใจ {e[0][1]}% | เงิน {e[0][2]}%\n"
            f"ไม้2 {_m(e[1][0],m)} | มั่นใจ {e[1][1]}% | เงิน {e[1][2]}%\n"
            f"ไม้3 {_m(e[2][0],m)} | มั่นใจ {e[2][1]}% | เงิน {e[2][2]}%\n"
            f"TP1 {_m(tp[0],m)} | TP2 {_m(tp[1],m)} | TP3 {_m(tp[2],m)}\n"
            f"SL {_m(sl,m)} ← ตัดขาดทุนทันทีถ้าหลุดนี้"
        )

    opt_block = ""
    if m in ("US","ETF"):
        opt_block = (f"\nOptions:\n"
                    f"CALL (ขาขึ้น) > {_m(s.price+s.atr14,m)} | DTE 7–21 วัน\n"
                    f"PUT  (ขาลง)  < {_m(s.price-s.atr14,m)} | DTE 7–21 วัน\n"
                    f"Conf: {max(30,s.confidence-7)}%\n")

    return (
        f"{'🇹🇭' if m=='TH' else '🇺🇸'} {s.symbol} | {s.name}\n"
        f"{time_th()} | {_live_line(s)}\n"
        f"Session: {sess}\n"
        f"═══════════════════\n"
        f"{price_block}\n\n"
        f"มุมมอง: {vi} {s.view}\n"
        f"Score: {s.score}/100 [{_bar(s.score)}]\n"
        f"Prob ขึ้น: {s.prob_up}% | Conf: {s.confidence}% | Risk: {s.risk_grade}{ge}\n"
        f"{risk_sentence(s)}\n\n"
        f"คาดการณ์ 1–3 วัน:\n"
        f"สูงสุด: {_m(em['high_3d'],m)} (+{em['up_prob']}%)\n"
        f"ต่ำสุด:  {_m(em['low_3d'],m)} ({em['down_prob']}%)\n"
        f"Expected Move: ±{em['expected_pct']:.1f}%\n\n"
        f"Technical:\n"
        f"RSI {s.rsi14:.1f} | EMA50 {s.ema50:.2f} | Vol {s.rvol:.1f}x\n"
        f"Trend 1D {s.trend_1d} | Trend 1W {s.trend_1w}\n\n"
        f"{plan_block}\n"
        f"{opt_block}\n"
        f"Entry Score: {entry_score(s)}/10 | จังหวะเข้า: {'ดี ✅' if entry_score(s)>=6 else 'รอ ⏳'}\n\n"
        f"ข่าว: {s.news1 or 'N/A'}\n"
        f"สรุป: {s.key_reason}\n\n"
        f"📚 คำศัพท์:\n"
        f"RSI={s.rsi14:.0f} ({'ซื้อมากเกิน' if s.rsi14>70 else 'ขายมากเกิน' if s.rsi14<30 else 'ปกติ'}) "
        f"| Vol={s.rvol:.1f}x ({'สูงผิดปกติ' if s.rvol>=1.2 else 'ปกติ'})\n\n"
        f"Version : {VERSION}"
    )

# ─── Top5 (full universe, beginner-friendly) ──────────────────
_UNI = {"US":US_UNIVERSE,"CALL":CALL_UNIVERSE,"PUT":PUT_UNIVERSE,
        "TH":TH_UNIVERSE,"ETF":ETF_UNIVERSE,"PRE":PRE_UNIVERSE}

def build_top5(kind="US"):
    k = kind.upper().replace(" ","")
    if k in ("GOLD","ทอง","ทองคำ"): return build_gold()
    is_put = (k == "PUT")
    universe = _UNI.get(k, US_UNIVERSE)

    rows = []
    for sym in universe:
        try:
            s = _apply_rt(get_snapshot(sym))
            mk = market_of(sym)
            em = expected_move(s)
            plan = trade_plan(s)
            rank = (s.prob_up*0.4 + s.confidence*0.25 + entry_score(s)*5 +
                    (5 if s.rvol>=1.2 else 0) + (5 if s.price>s.ema50 else 0))
            if is_put: rank = 100 - s.prob_up
            rows.append({"sym":s.symbol,"mk":mk,"s":s,"plan":plan,"em":em,"rank":rank})
        except Exception:
            pass

    rows.sort(key=lambda r: r["rank"], reverse=True)
    gate_fn = (lambda r: r["s"].prob_up<50 or "BEAR" in str(r["s"].view).upper()) if is_put else \
              (lambda r: r["s"].prob_up>=55 and "BEAR" not in str(r["s"].view).upper())
    passed = [r for r in rows if gate_fn(r)][:5]
    rest   = [r for r in rows if not gate_fn(r)][:3]

    title = f"{'📉' if is_put else '📈'} Top5 {k} | {time_th()}"
    lines = [title, f"Universe: {len(universe)} ตัว | ผ่านเกณฑ์: {len(passed)} ตัว", ""]

    for i, r in enumerate(passed or rows[:5], 1):
        s=r["s"]; mk=r["mk"]; plan=r["plan"]; em=r["em"]
        ge = _grade_emoji(s.risk_grade)
        live_b = "🟢" if getattr(s,"is_live",False) else "🔴"
        if not plan.get("no_trade") and plan.get("entries"):
            e=plan["entries"][0]; tp=plan["tp"]; sl=plan["sl"]
            entry_str = f"Entry {_m(e[0],mk)} → TP1 {_m(tp[0],mk)} SL {_m(sl,mk)}"
        else:
            entry_str = "NO TRADE — รอสัญญาณชัดกว่านี้"
        lines.append(
            f"{i}. {live_b} {s.symbol} {ge}{s.risk_grade} | {_m(s.price,mk)}{_chg(s.price,s.prev_close)}\n"
            f"   Prob {s.prob_up}% | Conf {s.confidence}% | RSI {s.rsi14:.0f} | Vol {s.rvol:.1f}x\n"
            f"   {entry_str}\n"
            f"   3วัน: ▲{_m(em['high_3d'],mk)} ▼{_m(em['low_3d'],mk)}\n"
            f"   💡 {s.key_reason[:60]}"
        )

    if rest:
        lines += ["", f"เฝ้าดู (ไม่ผ่านเกณฑ์): " + " | ".join([f"{r['sym']}({r['s'].prob_up}%)" for r in rest])]

    lines += ["",
        f"📚 มือใหม่:\n"
        f"• 🟢=Live 🔴=Fallback | ✅=ผ่านเกณฑ์ ⛔=ยังไม่ผ่าน\n"
        f"• Entry ± 0.5% ถือว่าเข้าได้\n"
        f"• ใส่เงินไม่เกิน 10% ต่อตัว\n"
        f"• SL ตัดทันทีไม่ฝืน",
        "", f"Version : {VERSION}"]
    return "\n".join(lines)

# ─── Pre-market movers ────────────────────────────────────────
def build_premarket():
    movers = []
    for sym in PRE_UNIVERSE:
        try:
            s = _apply_rt(get_snapshot(sym))
            pre=s.premarket; prev=s.prev_close
            if pre and prev and prev>0:
                pct=(pre-prev)/prev*100
                movers.append((sym,pre,prev,pct,s))
        except Exception:
            pass
    movers.sort(key=lambda x: abs(x[3]), reverse=True)

    if not movers:
        return (f"⏰ Pre-Market Movers | {time_th()}\n"
                f"ยังไม่มีข้อมูล pre-market\n"
                f"(ตลาด US เปิด 4:00–9:30 ET)\n\nVersion : {VERSION}")

    lines = [f"⏰ Pre-Market Movers | {time_th()}",
             "ราคาก่อนตลาด US (4:00–9:30 ET)", ""]
    for i,(sym,pre,prev,pct,s) in enumerate(movers[:8],1):
        a="▲" if pct>=0 else "▼"
        plan=trade_plan(s); mk=market_of(sym)
        hint=""
        if abs(pct)>=2 and not plan.get("no_trade"):
            hint = f"\n   📍 Gap {'+' if pct>0 else ''}{pct:.1f}% — รอแท่งแรก 5 นาที ก่อนเข้า"
        lines.append(f"{i}. {sym} | ${pre:.2f} {a}{abs(pct):.2f}%{hint}")

    lines += ["",
        "📚 มือใหม่ — Gap Play Rules:",
        "• Gap ≥ +2% = โอกาสขาขึ้นต่อ แต่รอยืนยันก่อน",
        "• Gap ≤ -2% = อาจ Fill gap กลับ (ไม่ต้อง panic)",
        "• ดูแท่งแรก 5–15 นาที ค่อยตัดสินใจ",
        "• Volume pre-market เบา — ระวัง fake move",
        "", f"Version : {VERSION}"]
    return "\n".join(lines)

# ─── Help (beginner-friendly) ────────────────────────────────
def build_help():
    return f"""📱 V1419 — คู่มือใช้งาน
{'='*28}
💬 พิมพ์ชื่อหุ้นเพื่อดูข้อมูล:
  nvda / aapl / msft / qqq / spy
  scb / kbank / ptt / aot / gold

📈 สัญญาณซื้อ-ขาย:
  top5        → หุ้น US น่าซื้อวันนี้
  top5 call   → สัญญาณขาขึ้น (CALL)
  top5 put    → สัญญาณขาลง (PUT)
  top5 th     → หุ้นไทยน่าสนใจ
  top5 etf    → ETF น่าซื้อ

🔍 สแกนตลาด:
  scan        → สแกนทั้งตลาด
  scan us     → สแกน US
  scan th     → สแกนไทย

🏆 ทองคำ:
  gold / ทอง  → ราคาทอง + แผนเทรด

⏰ ก่อนตลาดเปิด:
  premarket   → หุ้นที่ขยับก่อนตลาด

🌍 ภาพรวมตลาด:
  market      → Fear&Greed + Sector

📐 คำนวณขนาดไม้:
  kelly       → Kelly Criterion

🧭 สถานะระบบ:
  status      → API health check
  api nvda    → เช็ค API รายหุ้น

📚 คำศัพท์:
  rsi / ema / atr / sl / tp / kelly

Version : {VERSION}"""

# ─── Glossary ────────────────────────────────────────────────
def build_glossary(term=""):
    t = term.lower().strip()
    if t in _GLOSSARY:
        return f"📚 {t.upper()}\n{_GLOSSARY[t]}\n\nVersion : {VERSION}"
    all_terms = "\n".join([f"• {k}: {v[:50]}..." for k,v in _GLOSSARY.items()])
    return f"📚 คำศัพท์การเทรด\n\n{all_terms}\n\nพิมพ์ชื่อคำศัพท์เพื่อดูรายละเอียด\n\nVersion : {VERSION}"

# ─── Dispatch ─────────────────────────────────────────────────
def dispatch(text):
    t = (text or "").strip()
    low = t.lower()
    c = low.replace(" ","")

    if c in {"help","คำสั่ง","เมนู","v1419","v1418","v1417","v1416","v1415","v1414","v1413"}:
        return build_help()
    if c in {"scan","scanner","global","สแกน","สแกนตลาด","ทั้งตลาด"}:
        return global_scan_message("GLOBAL")
    if c in {"scanus","สแกนus"}: return global_scan_message("US")
    if c in {"scanth","สแกนไทย"}: return global_scan_message("TH")
    if c in {"scanetf","สแกนetf"}: return global_scan_message("ETF")
    if c in {"live","livescan","สแกนสด"}: return global_scan_message("GLOBAL")
    if low.startswith("live "): return build_stock(t.split(None,1)[1])
    if c in {"status","health","api","สถานะ","สถานะระบบ","ตรวจระบบ","เช็คระบบ","dashboard"}:
        return unified_control_center()
    if low.startswith("api "):
        return symbol_api_status(t.split()[1] if len(t.split())>1 else "NVDA")
    if c in {"gold","ทอง","ทองคำ","top5gold","xauusd","gold/"}: return build_gold()
    if c in {"top5","top5us","topus","หุ้นน่าซื้อ","หุ้นวันนี้"}: return build_top5("US")
    if c in {"top5call","topcall","call","คอล","สัญญาณขึ้น"}: return build_top5("CALL")
    if c in {"top5put","topput","put","พุต","สัญญาณลง"}: return build_top5("PUT")
    if c in {"top5th","topthai","top5thai","หุ้นไทย","หุ้นไทยน่าสนใจ"}: return build_top5("TH")
    if c in {"top5etf","topetf","etf"}: return build_top5("ETF")
    if c in {"premarket","ก่อนตลาด","premover"}: return build_premarket()
    if c in {"market","สภาพตลาด","ภาวะตลาด","feargreed","fear","greed","sector"}:
        return build_market()
    if c in {"kelly","kellysizing","sizing","ขนาดไม้"}: return build_kelly()
    if c in {"คำศัพท์","glossary","term","terms"}: return build_glossary()
    if c in _GLOSSARY: return build_glossary(c)
    if t: return build_stock(t)
    return None

# ─── V1420 Trading Commands ───────────────────────────────────
def _trading_commands(c, t, low):
    """Handle paper + live broker commands."""
    try:
        from v1420_trading_engine.broker import broker_status_text, place_order, get_account_info
        from v1420_trading_engine.paper_engine import (
            paper_status_text, open_paper_trade, close_paper_trade, get_open_trades
        )
    except Exception as e:
        return f"Trading engine error: {e}\n\nVersion : {VERSION}"

    # Broker / account status
    if c in {"broker","webull","account","บัญชี","พอร์ต","portfolio"}:
        return broker_status_text()

    # Paper summary
    if c in {"paper","papertrade","paperstatus","เปเปอร์","ผลเทรด","สรุปเทรด"}:
        return paper_status_text()

    # Open paper trade: "เปิด NVDA 1" or "open NVDA 1 185.50"
    if low.startswith("เปิด ") or low.startswith("open "):
        parts = t.split()
        if len(parts) >= 3:
            try:
                sym  = parts[1].upper()
                qty  = int(parts[2])
                entry = float(parts[3]) if len(parts)>3 else 0
                from v1413_worldclass_line_os.core.market_brain import get_snapshot, trade_plan
                s = get_snapshot(sym)
                plan = trade_plan(s)
                if not entry: entry = s.price or 0
                tp1 = plan["tp"][0] if plan.get("tp") else round(entry*1.02,2)
                tp2 = plan["tp"][1] if plan.get("tp") and len(plan["tp"])>1 else round(entry*1.04,2)
                sl  = plan.get("sl") or round(entry*0.98,2)
                trade_id = open_paper_trade(sym,"BUY",qty,entry,tp1,tp2,sl,
                                            score=s.score,conf=s.confidence)
                return (f"✅ เปิด Paper Trade #{trade_id}\n"
                       f"{sym} BUY {qty} หุ้น\n"
                       f"Entry: ${entry:.2f}\n"
                       f"TP1: ${tp1:.2f} | TP2: ${tp2:.2f}\n"
                       f"SL: ${sl:.2f}\n\n"
                       f"พิมพ์ 'ปิด {trade_id} [ราคา]' เพื่อปิด\n"
                       f"Version : {VERSION}")
            except Exception as e:
                return f"เปิด trade error: {e}"

    # Close paper trade: "ปิด 1 185.50" or "close 1 185.50"
    if low.startswith("ปิด ") or low.startswith("close "):
        parts = t.split()
        if len(parts) >= 3:
            try:
                tid   = int(parts[1])
                price = float(parts[2])
                result = close_paper_trade(tid, price)
                pnl = result.get("pnl",0)
                wr  = result.get("r_multiple",0)
                e   = "🟢 กำไร" if pnl>=0 else "🔴 ขาดทุน"
                return (f"{e} ปิด Trade #{tid}\n"
                       f"Exit: ${price:.2f}\n"
                       f"P&L: ${pnl:+,.2f} ({result.get('pnl_pct',0):+.2f}%)\n"
                       f"R-Multiple: {wr:+.2f}R\n\n"
                       f"พิมพ์ 'paper' เพื่อดูสรุป\n"
                       f"Version : {VERSION}")
            except Exception as e:
                return f"ปิด trade error: {e}"

    return None

# Patch dispatch to include trading commands
_original_dispatch = dispatch
def dispatch(text):
    t = (text or "").strip()
    low = t.lower()
    c = low.replace(" ","")
    # Try trading commands first
    result = _trading_commands(c, t, low)
    if result:
        return result
    # Fall through to original
    return _original_dispatch(text)
