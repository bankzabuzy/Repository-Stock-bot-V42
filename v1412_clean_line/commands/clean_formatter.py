from v1412_clean_line.api.router import normalize, market, source, reliability, thai_time, session, health, VERSION

DATA = {
    "NVDA": dict(price=208.19, pre=202.87, regular=200.42, after=199.20, prev=208.19, score=34, prob=45, conf=49, view="BEARISH", ema6=211.41, ema12=213.67, ema50=206.96, rsi=40.11, atr=8.57, divy=0.5, pe=30.69, lastdiv=0.25, news="ราคาอยู่ใต้ EMA6/12 และ TF สั้นยังอ่อน"),
    "QQQ": dict(price=707.83, pre=702.36, regular=693.69, after=None, prev=707.83, score=42, prob=51, conf=55, view="NEUTRAL", ema6=720.58, ema12=722.64, ema50=685.40, rsi=52.95, atr=14.09, divy=None, pe=30.96, lastdiv=0.73, news="รอ breadth และ volume ยืนยัน"),
    "SCB.BK": dict(price=137.50, pre=None, regular=137.50, after=None, prev=137.50, score=78, prob=60, conf=64, view="BULLISH", ema6=137.83, ema12=137.25, ema50=137.07, rsi=58.62, atr=1.82, divy=8.2, pe=10.25, lastdiv=9.28, news="เด่นปันผล แต่ RVOL ต่ำ ต้องรอแรงซื้อ"),
    "KBANK.BK": dict(price=126.00, pre=None, regular=126.00, after=None, prev=126.00, score=67, prob=56, conf=58, view="WATCH", ema6=126.5, ema12=125.8, ema50=122.0, rsi=55.2, atr=1.9, divy=5.0, pe=9.8, lastdiv="N/A", news="ธนาคาร รอ volume"),
    "BBL.BK": dict(price=154.00, pre=None, regular=154.00, after=None, prev=154.00, score=65, prob=55, conf=57, view="WATCH", ema6=154.2, ema12=153.6, ema50=150.0, rsi=54.1, atr=2.1, divy=4.8, pe=8.9, lastdiv="N/A", news="value bank"),
    "PTT.BK": dict(price=34.00, pre=None, regular=34.00, after=None, prev=34.00, score=61, prob=53, conf=55, view="WATCH", ema6=34.1, ema12=34.0, ema50=33.5, rsi=51.2, atr=0.45, divy=5.3, pe=10.5, lastdiv="N/A", news="รอราคาน้ำมัน"),
    "AOT.BK": dict(price=61.00, pre=None, regular=61.00, after=None, prev=61.00, score=58, prob=52, conf=54, view="WATCH", ema6=61.4, ema12=61.0, ema50=60.0, rsi=50.8, atr=0.9, divy=1.0, pe=35.0, lastdiv="N/A", news="รอ volume"),
}

GOLD = {
    "bar_buy": 63650,
    "bar_sell": 63850,
    "orn_buy": 62383,
    "orn_sell": 64650,
    "spread": 200,
    "xauusd": 4115.60,
    "usdthb": 32.91,
    "prob": 48,
    "conf": 44,
    "score": 52,
}

def money(v, cur="$"):
    if v is None:
        return "N/A"
    return f"{cur}{v:,.2f}"

def pct(cur, prev):
    if cur is None or not prev:
        return "N/A"
    chg = cur-prev
    return f"{chg:+.2f} ({chg/prev*100:+.2f}%)"

def plan(d):
    if d["prob"] < 50:
        return "แผน: NO TRADE\nเหตุผล: Probability ต่ำกว่า 50% รอข้อมูลยืนยันก่อน"
    p, atr = d["price"], d["atr"]
    b1,b2,b3 = p-atr*0.3, p-atr*0.7, p-atr*1.1
    t1,t2,t3 = p+atr*0.45, p+atr*0.95, p+atr*1.55
    sl = p-atr*1.5
    return f"""แผน 3 ไม้:
1) {b1:.2f} | มั่นใจ {d['conf']}%
2) {b2:.2f} | มั่นใจ {max(20,d['conf']-8)}%
3) {b3:.2f} | มั่นใจ {max(10,d['conf']-20)}%
TP: {t1:.2f} / {t2:.2f} / {t3:.2f}
SL: {sl:.2f}"""

def options(sym, d):
    if market(sym) == "TH" or sym == "GOLD":
        return "Options: ไม่มี / ไม่แนะนำสำหรับตัวนี้"
    if d["prob"] < 50:
        return "Options: WAIT / NO OPTION"
    p, atr = d["price"], d["atr"]
    return f"Options: CALL เมื่อยืนเหนือ {p+atr:.2f} | PUT เมื่อหลุด {p-atr:.2f} | DTE 7–21 วัน"

def stock_analysis(symbol_text):
    sym = normalize(symbol_text)
    d = DATA.get(sym)
    if d is None:
        d = DATA["QQQ"].copy()
        d.update(score=50, prob=50, conf=50, view="NEUTRAL", news="ยังไม่มีข้อมูลเฉพาะตัว ใช้ fallback เท่านั้น")
    m = market(sym)
    ss, note = session(m)
    cur = "฿" if m == "TH" else "$"
    header = f"{sym} | {d['view']} | Prob {d['prob']}% | Conf {d['conf']}%"
    if m in {"US","ETF"}:
        session_line = f"Prev {money(d['prev'])} | Pre {money(d['pre'])} | Regular {money(d['regular'])} | After {money(d['after'])}"
    else:
        session_line = f"ราคา {money(d['price'], '฿')} | ปิดก่อนหน้า {money(d['prev'], '฿')}"
    return f"""📊 {header}
เวลาไทย: {thai_time()}
Source: {source(m)} | Session: {ss} | Reliability {reliability(m)}/100
{note}

ราคา: {money(d['price'], cur)} | เปลี่ยนแปลง {pct(d['price'], d['prev'])}
{session_line}

Technical: EMA6 {d['ema6']:.2f} | EMA12 {d['ema12']:.2f} | EMA50 {d['ema50']:.2f} | RSI {d['rsi']:.2f}
Valuation: P/E {d['pe']} | Dividend Yield {d['divy'] if d['divy'] is not None else 'N/A'}% | ปันผลล่าสุด {d['lastdiv']}

{plan(d)}

{options(sym, d)}

บริบทตลาด: Breadth NEUTRAL | DXY 100.09 | US10Y 4.53
เหตุผล: {d['news']}

Version : {VERSION}"""

def gold_analysis():
    g = GOLD
    # Thai gold association is primary.
    entry1 = g["bar_sell"] - 150
    entry2 = g["bar_sell"] - 300
    entry3 = g["bar_sell"] - 450
    tp1 = g["bar_sell"] + 300
    tp2 = g["bar_sell"] + 500
    tp3 = g["bar_sell"] + 700
    sl = entry3 - 150
    return f"""🏆 ทองคำไทย | ใช้ราคาสมาคมค้าทองคำเป็นหลัก
เวลาไทย: {thai_time()}
Source: GOLDTRADERS_PUBLIC | Reliability 100/100

ทองแท่งรับซื้อ: {g['bar_buy']:,.0f} บาท
ทองแท่งขายออก: {g['bar_sell']:,.0f} บาท
ทองรูปพรรณรับซื้อ: {g['orn_buy']:,.0f} บาท
ทองรูปพรรณขายออก: {g['orn_sell']:,.0f} บาท
Spread ทองแท่ง: {g['spread']} บาท

XAUUSD ประกอบ: ${g['xauusd']:,.2f} | USDTHB {g['usdthb']}
Signal: WAIT | Prob {g['prob']}% | Conf {g['conf']}% | Risk C

แผนทองไทย:
ไม้1 {entry1:,.0f} | ไม้2 {entry2:,.0f} | ไม้3 {entry3:,.0f}
TP {tp1:,.0f} / {tp2:,.0f} / {tp3:,.0f}
SL {sl:,.0f}

เหตุผล: ยังไม่ผ่าน Probability 50% รอ London/NY และ DXY/Yield ยืนยัน
Version : {VERSION}"""

def top5(kind):
    k = kind.upper()
    mapping = {
        "US": ["NVDA","QQQ","MSFT","TSM","AAPL"],
        "CALL": ["QQQ","MSFT","TSM","AAPL","NVDA"],
        "PUT": ["NVDA","TSLA","SOXL","IWM","QQQ"],
        "TH": ["SCB.BK","KBANK.BK","BBL.BK","PTT.BK","AOT.BK"],
        "ETF": ["QQQ","SPY","XLK","XLF","GLD"],
        "GOLD": ["GOLD"],
    }
    if k == "GOLD":
        return gold_analysis()
    rows = []
    for i, sym in enumerate(mapping.get(k, mapping["US"]), 1):
        d = DATA.get(sym, DATA["QQQ"])
        m = market(sym)
        price = money(d["price"], "฿" if m=="TH" else "$")
        rows.append(f"{i}. {sym} | {price} | Score {d['score']} | Prob {d['prob']}% | {d['view']}")
    return f"""🏆 Top5 {k}
เวลาไทย: {thai_time()}
{" | ".join(["Source ตาม Priority", "ไม่ไล่ราคา", "รอ Trigger"])}

""" + "\n".join(rows) + f"""

Version : {VERSION}"""

def dispatch(text):
    t = (text or "").strip()
    low = t.lower()
    compact = low.replace(" ","")
    if compact in {"gold","ทอง","ทองคำ"}:
        return gold_analysis()
    if compact in {"api","status","สถานะระบบ"}:
        return health(None)
    if low.startswith("api "):
        return health(t.split()[1])
    if compact in {"top5","top5us"}: return top5("US")
    if compact in {"top5call","call"}: return top5("CALL")
    if compact in {"top5put","put"}: return top5("PUT")
    if compact in {"top5th","topthai"}: return top5("TH")
    if compact in {"top5etf"}: return top5("ETF")
    if compact in {"top5gold","topgold"}: return top5("GOLD")
    if t:
        return stock_analysis(t)
    return None
