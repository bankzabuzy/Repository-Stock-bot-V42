from v1410_master_os_enhanced.api_router.router import price_source_note, api_status_text

VERSION = "V1410_MASTER_OS_ENHANCED"

SAMPLE = {
    "US": [
        {"symbol":"NVDA","side":"CALL","score":88,"prob":82,"conf":86,"risk":"A","regime":"UPTREND","entry":"รอยืนเหนือ pre-market high","reason":"AI/Semiconductor leader + liquidity สูง"},
        {"symbol":"TSM","side":"CALL","score":84,"prob":78,"conf":80,"risk":"A","regime":"UPTREND","entry":"รอย่อไม่หลุด VWAP","reason":"Foundry leader + sector แข็ง"},
        {"symbol":"MSFT","side":"CALL","score":80,"prob":73,"conf":77,"risk":"A","regime":"UPTREND","entry":"รอ breakout ยืนยัน","reason":"Quality mega cap"},
        {"symbol":"QQQ","side":"CALL","score":76,"prob":69,"conf":72,"risk":"B","regime":"MIXED","entry":"รอ breadth ยืนยัน","reason":"ETF นำตลาด"},
        {"symbol":"AAPL","side":"CALL","score":72,"prob":65,"conf":70,"risk":"B","regime":"RANGE","entry":"รอย่อเข้าโซน","reason":"Quality defensive growth"},
    ],
    "TH": [
        {"symbol":"SCB.BK","side":"BUY","score":78,"prob":60,"conf":64,"risk":"B","regime":"UPTREND","entry":"ใช้ SET_LAST_CLOSE/Yahoo .BK fallback","reason":"ปันผลสูง + valuation ไม่แพง"},
        {"symbol":"KBANK.BK","side":"BUY","score":73,"prob":58,"conf":62,"risk":"B","regime":"UPTREND","entry":"รอย่อไม่หลุด EMA50","reason":"กลุ่มธนาคารแข็ง"},
        {"symbol":"BBL.BK","side":"BUY","score":71,"prob":57,"conf":60,"risk":"B","regime":"UPTREND","entry":"ทยอยสะสม","reason":"value + dividend"},
        {"symbol":"PTT.BK","side":"WATCH","score":66,"prob":55,"conf":58,"risk":"C","regime":"RANGE","entry":"รอ oil confirm","reason":"energy rotation"},
        {"symbol":"AOT.BK","side":"WATCH","score":62,"prob":53,"conf":56,"risk":"C","regime":"RANGE","entry":"รอ volume","reason":"reopening/traffic"},
    ],
    "ETF": [
        {"symbol":"SPY","side":"CALL","score":79,"prob":70,"conf":76,"risk":"A","regime":"UPTREND","entry":"รอ breadth > 55","reason":"ตลาดกว้าง"},
        {"symbol":"QQQ","side":"CALL","score":76,"prob":69,"conf":72,"risk":"B","regime":"MIXED","entry":"รอ XLK ยืนยัน","reason":"growth momentum"},
        {"symbol":"XLK","side":"CALL","score":74,"prob":66,"conf":70,"risk":"B","regime":"UPTREND","entry":"รอ sector strength","reason":"tech rotation"},
        {"symbol":"XLF","side":"WATCH","score":68,"prob":60,"conf":64,"risk":"B","regime":"UPTREND","entry":"รอ yield confirm","reason":"financial rotation"},
        {"symbol":"GLD","side":"WATCH","score":65,"prob":58,"conf":62,"risk":"B","regime":"MIXED","entry":"รอ DXY/Yield","reason":"gold hedge"},
    ],
    "GOLD": [
        {"symbol":"GOLD","side":"WAIT","score":70,"prob":62,"conf":66,"risk":"B","regime":"MIXED","entry":"รอ London/NY session","reason":"GoldTraders + GoldAPI + XAUUSD"},
        {"symbol":"XAUUSD","side":"WAIT","score":68,"prob":60,"conf":64,"risk":"B","regime":"MIXED","entry":"รอ break structure","reason":"spot gold"},
        {"symbol":"GC=F","side":"WATCH","score":63,"prob":55,"conf":58,"risk":"C","regime":"RANGE","entry":"ใช้เป็น fallback","reason":"futures proxy"},
        {"symbol":"GLD","side":"WATCH","score":62,"prob":55,"conf":58,"risk":"C","regime":"RANGE","entry":"ETF proxy","reason":"gold ETF"},
        {"symbol":"USDTHB","side":"WATCH","score":58,"prob":52,"conf":55,"risk":"C","regime":"RANGE","entry":"ใช้คำนวณทองไทย","reason":"FX conversion"},
    ],
    "PUT": [
        {"symbol":"NVDA","side":"PUT","score":70,"prob":61,"conf":65,"risk":"B","regime":"PULLBACK","entry":"หลุด support + TF bearish","reason":"ใช้เฉพาะเมื่อต่ำกว่า risk gate"},
        {"symbol":"QQQ","side":"PUT","score":68,"prob":60,"conf":63,"risk":"B","regime":"PULLBACK","entry":"หลุด VWAP + breadth risk-off","reason":"index hedge"},
        {"symbol":"TSLA","side":"PUT","score":66,"prob":58,"conf":61,"risk":"C","regime":"VOLATILE","entry":"หลุด low สำคัญ","reason":"high beta"},
        {"symbol":"SOXL","side":"PUT","score":64,"prob":56,"conf":60,"risk":"C","regime":"VOLATILE","entry":"ใช้ขนาดเล็ก","reason":"leveraged ETF"},
        {"symbol":"IWM","side":"PUT","score":60,"prob":54,"conf":58,"risk":"C","regime":"WEAK","entry":"ถ้า small cap breadth อ่อน","reason":"risk-off proxy"},
    ],
}

def row_line(i, item):
    note = price_source_note(item["symbol"])
    return (
        f"{i}. {item['symbol']} | {item['side']} | Score {item['score']}/100 | Prob {item['prob']}% | Conf {item['conf']}% | Risk {item['risk']}\n"
        f"   Regime: {item['regime']} | Entry: {item['entry']}\n"
        f"   Source: {note['source']} | Reliability {note['reliability']}/100 | Market: {note['market']}\n"
        f"   เหตุผล: {item['reason']}"
    )

def build_top5(kind):
    k = kind.upper()
    if k in {"CALL"}:
        data = [x for x in SAMPLE["US"] if x["side"] == "CALL"]
        title = "🏆 TOP5 CALL / EARLY LONG SETUP"
    elif k in {"PUT"}:
        data = SAMPLE["PUT"]
        title = "🏆 TOP5 PUT / HEDGE SETUP"
    elif k in {"US"}:
        data = SAMPLE["US"]
        title = "🏆 TOP5 US STOCKS"
    elif k in {"TH", "THAI"}:
        data = SAMPLE["TH"]
        title = "🏆 TOP5 THAI STOCKS"
    elif k in {"ETF"}:
        data = SAMPLE["ETF"]
        title = "🏆 TOP5 ETF"
    elif k in {"GOLD"}:
        data = SAMPLE["GOLD"]
        title = "🏆 TOP5 GOLD / XAUUSD"
    else:
        data = SAMPLE["US"]
        title = "🏆 TOP5 MASTER"
    lines = [title, "Market Reference: Prev Close / Pre-market / After-hours ตาม source ที่พร้อม", ""]
    lines += [row_line(i, item) for i,item in enumerate(data[:5], 1)]
    lines.append("")
    lines.append("กฎใช้งาน:")
    lines.append("- Probability < 50 = NO TRADE")
    lines.append("- Risk C/D = เฝ้าดูหรือลดขนาดไม้")
    lines.append("- Early Entry ต้องรอ Volume + Breadth + Breakout ยืนยัน")
    lines.append("")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)
