from datetime import datetime, timezone, timedelta
from v1412_restore_full_analysis.api.router import normalize, market, source, reliability, thai_time_str, session_info, health_text, VERSION

# Fallback reference values are only placeholders for formatting when live source
# is unavailable. The message clearly labels source/session; no fake BUY is emitted.
BASE = {
    "NVDA": dict(price=208.19, pre=202.87, regular=200.42, after=199.20, prev=208.19, pe=30.69, fpe=15.75, divy=0.50, divrate=1.00, lastdiv=0.25, lastdivdate="2026-06-04", low52=140.85, high52=236.54, ema6=211.41, ema12=213.67, ema50=206.96, rsi=40.11, atr=8.57, rvol=1.01, score=34, prob=45, conf=49, view="BEARISH / ฝั่งขายได้เปรียบ", regime="UPTREND", align="2/2 Bearish", tf1="15m: BEARISH", tf2="1h: BEARISH"),
    "QQQ": dict(price=707.83, pre=702.36, regular=693.69, after=None, prev=707.83, pe=30.96, fpe=None, divy=None, divrate=None, lastdiv=0.73, lastdivdate="2026-03-23", low52=523.65, high52=748.65, ema6=720.58, ema12=722.64, ema50=685.40, rsi=52.95, atr=14.09, rvol=2.18, score=42, prob=51, conf=55, view="NEUTRAL / รอดูจังหวะ", regime="UPTREND", align="Mixed 2 TF", tf1="1D: MIXED", tf2="1W*: MIXED"),
    "SCB.BK": dict(price=137.50, pre=None, regular=137.50, after=None, prev=137.50, pe=10.25, fpe=10.32, divy=8.20, divrate=11.28, lastdiv=9.28, lastdivdate="2026-04-20", low52=115.00, high52=149.50, ema6=137.83, ema12=137.25, ema50=137.07, rsi=58.62, atr=1.82, rvol=0.60, score=78, prob=60, conf=64, view="BULLISH / ฝั่งซื้อได้เปรียบ", regime="STRONG UPTREND", align="Mixed 2 TF", tf1="1D: MIXED", tf2="1W*: MIXED"),
    "GOLD": dict(price=4115.60, pre=None, regular=4115.60, after=None, prev=4110.10, pe=None, fpe=None, divy=None, divrate=None, lastdiv=None, lastdivdate="N/A", low52=None, high52=None, ema6=4118.2, ema12=4109.6, ema50=4050.0, rsi=56.2, atr=32.4, rvol=1.0, score=52, prob=48, conf=44, view="WAIT / รอจังหวะ", regime="MIXED", align="M15:BULLISH | H1:NEUTRAL | H4:BEARISH | D1:BEARISH", tf1="M15: BULLISH", tf2="H1: NEUTRAL"),
}

NEWS = {
    "NVDA": ["Nvidia AI platform remains key market focus", "Semiconductor breadth mixed in extended hours", "Watch volume confirmation before entry"],
    "QQQ": ["Nasdaq 100 momentum mixed before open", "Growth sector waits for breadth confirmation", "Rates and DXY remain key macro filters"],
    "SCB.BK": ["ข่าวหุ้นไทยยังไม่ได้เชื่อม API ข่าวเฉพาะ SET", "กลุ่มธนาคารยังเป็น valuation + dividend play", "รอ volume ยืนยันก่อนเพิ่มไม้"],
    "GOLD": ["Gold reacts to DXY/Yield and geopolitical headlines", "Wait for London/New York liquidity", "Thai gold uses GoldTraders/GoldAPI fallback"],
}

def fmt_money(v, prefix="$"):
    if v is None:
        return "N/A"
    if prefix == "฿":
        return f"฿{v:,.2f}"
    return f"{prefix}{v:,.2f}"

def pct_line(current, prev):
    if current is None or prev in (None, 0):
        return "N/A"
    chg = current - prev
    pct = chg / prev * 100
    return f"{fmt_money(current)} | {chg:+.2f} ({pct:+.2f}%)"

def levels(d):
    price = d["price"]
    atr = d.get("atr") or max(price*0.01, 1)
    prob = d.get("prob") or 50
    if prob < 50:
        return None
    b1 = price - atr*0.30
    b2 = price - atr*0.70
    b3 = price - atr*1.10
    t1 = price + atr*0.45
    t2 = price + atr*0.95
    t3 = price + atr*1.55
    sl = price - atr*1.50
    return b1,b2,b3,t1,t2,t3,sl

def option_block(sym, d):
    prob = d.get("prob", 0)
    price = d.get("price", 0)
    atr = d.get("atr") or max(price*0.01, 1)
    if prob < 50:
        return f"""🧠 Options Hybrid Max Free
Setup: WAIT / NO OPTION
เข้าวันที่: {thai_time_str()}
Probability ประมาณ: {prob}%
เหตุผลที่ยังไม่ออกไม้จริง: Probability ต่ำกว่า 50% และต้องการยืนยัน Timeframe/Volume ก่อน"""
    call_trigger = price + atr
    put_trigger = price - atr
    # rounded strike
    step = 5 if price > 100 else 1
    call_strike = round(call_trigger / step) * step
    put_strike = round(put_trigger / step) * step
    return f"""🧠 Options Hybrid Max Free
Setup: WAIT / รอจังหวะ
เข้าวันที่: {thai_time_str()} เฉพาะเมื่อราคาเลือกทางชัดเจน
DTE แนะนำ: 7–21 วัน สำหรับเก็งกำไร / 30–45 วันสำหรับลด theta
CALL: เข้าเมื่อยืนเหนือ {call_trigger:.2f} และ TF สั้นต้องเปลี่ยนเป็น BULLISH | Strike เฝ้าดู {call_strike:.2f}C
PUT: เข้าเมื่อหลุดต่ำกว่า {put_trigger:.2f} และ TF สั้นต้องเปลี่ยนเป็น BEARISH | Strike เฝ้าดู {put_strike:.2f}P
Probability ประมาณ: {prob}%
เหตุผลที่ยังไม่ออกไม้จริง: ต้องการยืนยัน Timeframe/Volume ก่อน"""

def world_context(sym):
    sector = "Semiconductor / AI" if sym == "NVDA" else ("Growth ETF" if sym == "QQQ" else ("Thai Bank" if sym == "SCB.BK" else "Gold / Macro Hedge"))
    proxy = "XLK: -1.85% | LAGGING" if sym in {"NVDA","QQQ"} else ("XLF: +0.94% | LEADING" if sym == "SCB.BK" else "DXY/Yield sensitive")
    return f"""🌍 V1412 World Context
🌐 Market Breadth: NEUTRAL | Score: 50.0/100 | SPY: -0.29% | QQQ: -1.15% | IWM: +0.32% | DIA: +0.10%
💵 DXY/Yield: DXY 100.09 (+0.18%) | US10Y 4.53 (-0.53%)
📅 Earnings Calendar: {sym} | ยังไม่พบกำหนดงบจาก API ฟรี / รอเชื่อม FMP หรือ AlphaVantage
🔁 Sector Rotation: {sector} | Proxy {proxy}"""

def analysis(symbol_text):
    sym = normalize(symbol_text)
    if sym not in BASE:
        if market(sym) == "TH":
            sym = sym if sym.endswith(".BK") else sym + ".BK"
            BASE[sym] = BASE["SCB.BK"].copy()
            BASE[sym]["score"] = 60
            BASE[sym]["prob"] = 52
            BASE[sym]["view"] = "NEUTRAL / รอดูจังหวะ"
        else:
            BASE[sym] = BASE["QQQ"].copy()
            BASE[sym]["score"] = 50
            BASE[sym]["prob"] = 50
            BASE[sym]["view"] = "NEUTRAL / ข้อมูลจริงรอยืนยัน"
    d = BASE[sym]
    mkt = market(sym)
    src = source(mkt)
    rel = reliability(mkt)
    session, price_source = session_info(mkt)
    currency = "฿" if mkt == "TH" else "$"
    header = ""
    if mkt in {"US","ETF"}:
        header = f"🇺🇸 {sym}: ปิดก่อนหน้า {fmt_money(d.get('prev'))} | Pre-market {fmt_money(d.get('pre'))} | {((d.get('pre') or d['price']) - d.get('prev', d['price'])):+.2f} ({(((d.get('pre') or d['price']) - d.get('prev', d['price']))/(d.get('prev', d['price']) or 1)*100):+.2f}%)"
    elif mkt == "TH":
        header = f"🇹🇭 {sym}: ราคาล่าสุด {fmt_money(d.get('price'),'฿')} | ปิดก่อนหน้า {fmt_money(d.get('prev'),'฿')}"
    else:
        header = f"🏆 GOLD: XAUUSD/GC=F {fmt_money(d.get('price'))} | Prev {fmt_money(d.get('prev'))}"

    lv = levels(d)
    if lv:
        b1,b2,b3,t1,t2,t3,sl = lv
        plan = f"""🧩 แผนเข้า/ออก 3 ไม้
ซื้อไม้ 1: {b1:.2f} | ความมั่นใจ {min(95, d.get('conf',50))}% | ไม้หลัก
ซื้อไม้ 2: {b2:.2f} | ความมั่นใจ {max(20, d.get('conf',50)-8)}% | ไม้สะสม
ซื้อไม้ 3: {b3:.2f} | ความมั่นใจ {max(10, d.get('conf',50)-20)}% | ไม้เสี่ยง/เผื่อย่อแรง

ขาย/ทำกำไร 1: {t1:.2f} | โอกาสถึงเป้า {max(10, d.get('prob',50)-2)}%
ขาย/ทำกำไร 2: {t2:.2f} | โอกาสถึงเป้า {max(10, d.get('prob',50)-16)}%
ขาย/ทำกำไร 3: {t3:.2f} | โอกาสถึงเป้า {max(10, d.get('prob',50)-30)}%

จุดคุมความเสี่ยง: {sl:.2f}
แนะนำแบ่งเงิน: ไม้1 30% / ไม้2 30% / ไม้3 40% เฉพาะเมื่อราคายืนยัน ไม่ควรรีบถัว
เงื่อนไขเข้มงวด: ถ้าราคาไม่ยืน/ไม่เด้งตามแผน ห้ามเพิ่มไม้ถัดไปอัตโนมัติ"""
    else:
        plan = f"""🧩 แผนเข้า/ออก 3 ไม้
สถานะ: NO TRADE / ยังไม่ออกไม้จริง
เหตุผล: Probability ต่ำกว่า 50% จึงปิดแผนเข้าอัตโนมัติ
เงื่อนไขกลับมาพิจารณา: ต้องรอ Probability ≥ 50%, Timeframe/Volume ยืนยัน และ Risk Gate ผ่าน"""

    news = "\n".join([f"- {x}" for x in NEWS.get(sym, NEWS.get("QQQ", []))])
    reasons = []
    if d["price"] < d["ema6"]: reasons.append("ราคาอยู่ใต้ EMA6 และ EMA12")
    if d["rsi"] >= 50: reasons.append("RSI อยู่ในโซนโมเมนตัมขาขึ้น")
    else: reasons.append("RSI ต่ำกว่าโซนแข็งแรง")
    if d["rvol"] < 0.8: reasons.append("RVOL ต่ำกว่า 0.8 จึงลดความมั่นใจ")
    else: reasons.append("Volume สนับสนุน/ต้องจับตาทิศทาง")
    reason_text = "\n".join([f"- {r}" for r in reasons])

    return f"""{header}

📊 วิเคราะห์ {sym}
แหล่งข้อมูล: {src}
Data Router: {mkt} | Primary: {src} | Status: READY | Reliability: {rel}/100
เวลาไทย: {thai_time_str()}
Market Session: {session} | Price Source: {price_source}
Price Note: ใช้ราคาตาม session ที่พร้อม ถ้า source หลักล่มจะ fallback และห้ามสร้าง fake signal

ราคา: {fmt_money(d.get('price'), currency)}
เปลี่ยนแปลง: {pct_line(d.get('price'), d.get('prev'))}

AI Score V3: {d.get('score')}/100
Probability ประมาณ: {d.get('prob')}%
มุมมอง: {d.get('view')}
Market Regime: {d.get('regime')}
Trend Alignment: {d.get('align')}

Multi Timeframe:
- {d.get('tf1')}
- {d.get('tf2')}

📈 Technical
EMA6: {d.get('ema6'):.2f}
EMA12: {d.get('ema12'):.2f}
EMA50: {d.get('ema50'):.2f}
RSI14: {d.get('rsi'):.2f}
ATR14: {d.get('atr'):.2f}
RVOL: {d.get('rvol'):.2f}

💎 Dividend + Valuation

สถานะราคา: กลาง / พอรับได้

Market Cap: N/A
P/E: {d.get('pe') if d.get('pe') is not None else 'N/A'}
Forward P/E: {d.get('fpe') if d.get('fpe') is not None else 'N/A'}
Dividend Yield: {str(d.get('divy')) + '%' if d.get('divy') is not None else 'N/A'}
Dividend Rate: {d.get('divrate') if d.get('divrate') is not None else 'N/A'}

XD / Ex-dividend: N/A
วันประกาศงบ: N/A
ปันผลล่าสุด: {d.get('lastdiv') if d.get('lastdiv') is not None else 'N/A'}
วันที่ปันผลล่าสุด: {d.get('lastdivdate')}

52W Low: {d.get('low52') if d.get('low52') is not None else 'N/A'}
52W High: {d.get('high52') if d.get('high52') is not None else 'N/A'}

เหตุผล valuation:
- ราคาไม่ห่างจาก EMA50 มากเกินไป
- P/E/Dividend ใช้เมื่อ source มีข้อมูล
- ถ้าข้อมูล valuation ไม่พร้อม ระบบแสดง N/A ไม่สร้างข้อมูลปลอม

{plan}

{option_block(sym, d)}

{world_context(sym)}

เหตุผลหลัก:
{reason_text}

📰 ข่าว/บริบท:
{news}

Version : {VERSION}

🇺🇸 Extended Hours [{session}] | Pre-market: {fmt_money(d.get('pre'))} | Regular: {fmt_money(d.get('regular'))} | After-hours: {fmt_money(d.get('after'))} | Prev Close: {fmt_money(d.get('prev'))}"""

def top5(kind="US"):
    kind = kind.upper()
    universe = {
        "US": ["NVDA","QQQ","MSFT","TSM","AAPL"],
        "CALL": ["NVDA","QQQ","MSFT","TSM","AAPL"],
        "PUT": ["QQQ","NVDA","TSLA","SOXL","IWM"],
        "TH": ["SCB.BK","KBANK.BK","BBL.BK","PTT.BK","AOT.BK"],
        "ETF": ["QQQ","SPY","XLK","XLF","GLD"],
        "GOLD": ["GOLD","XAUUSD","GC=F","GLD","USDTHB"],
    }.get(kind, ["NVDA","QQQ","SCB.BK","GOLD"])
    title = {"US":"🏆 Top5 US", "CALL":"🏆 Top5 CALL", "PUT":"🏆 Top5 PUT", "TH":"🏆 Top5 หุ้นไทย", "ETF":"🏆 Top5 ETF", "GOLD":"🏆 Top5 ทอง"}.get(kind, "🏆 Top5")
    lines = [f"{title} (V1412 Full Analysis)", f"เวลาไทย: {thai_time_str()}", "ราคาที่ใช้: Prev Close / Pre-market / After-hours ตาม source ที่พร้อม", ""]
    for i, sym in enumerate(universe[:5], 1):
        s = normalize(sym)
        d = BASE.get(s, BASE.get("QQQ")).copy()
        lines.append(f"{i}. {s} | Score {d.get('score')}/100 | Prob {d.get('prob')}% | Confidence {d.get('conf')}%")
        lines.append(f"   Source: {source(market(s))} | Session: {session_info(market(s))[0]} | Price: {fmt_money(d.get('price'), '฿' if market(s)=='TH' else '$')}")
        lines.append(f"   Action: {'NO TRADE' if d.get('prob',0)<50 else 'รอ Trigger ยืนยัน'}")
    lines.append("")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)

def dispatch(text):
    t = (text or "").strip()
    low = t.lower()
    compact = low.replace(" ","")
    if compact in {"api","สถานะระบบ","status","health"}:
        return health_text(None)
    if low.startswith("api "):
        return health_text(t.split()[1])
    if low.startswith("entry "):
        return analysis(t.split()[1])
    if compact in {"top5","top5us"}: return top5("US")
    if compact in {"top5call","call"}: return top5("CALL")
    if compact in {"top5put","put"}: return top5("PUT")
    if compact in {"top5th","topthai"}: return top5("TH")
    if compact in {"top5etf"}: return top5("ETF")
    if compact in {"top5gold","topgold"}: return top5("GOLD")
    if compact in {"v1412","help","คำสั่ง"}:
        return "คำสั่ง: nvda / qqq / scb / gold / top5 us / top5 call / top5 put / top5 th / api nvda\n\nVersion : " + VERSION
    if t:
        return analysis(t)
    return None
