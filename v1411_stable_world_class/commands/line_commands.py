from v1411_stable_world_class.api.router import status, classify, normalize_symbol, best_provider, reliability, session_label
from v1411_stable_world_class.storage.queue import AlertQueue

VERSION = "V1419_MASTER_CLEAN_FINAL"

DATA = {
    "US": [
        ("NVDA","CALL",88,82,86,"A","รอทะลุ pre-market high / volume ยืนยัน"),
        ("TSM","CALL",84,78,80,"A","รอย่อไม่หลุด VWAP"),
        ("MSFT","CALL",80,73,77,"A","รอ breakout ยืนยัน"),
        ("QQQ","CALL",76,69,72,"B","รอ breadth > 55"),
        ("AAPL","CALL",72,65,70,"B","รอย่อเข้าโซน"),
    ],
    "CALL": [
        ("NVDA","CALL",88,82,86,"A","Early long setup"),
        ("TSM","CALL",84,78,80,"A","Sector leader"),
        ("MSFT","CALL",80,73,77,"A","Quality breakout"),
        ("QQQ","CALL",76,69,72,"B","ETF momentum"),
        ("XLK","CALL",74,66,70,"B","Tech rotation"),
    ],
    "PUT": [
        ("QQQ","PUT",70,61,65,"B","หลุด VWAP + Breadth risk-off"),
        ("NVDA","PUT",68,60,63,"B","หลุด support สำคัญ"),
        ("TSLA","PUT",66,58,61,"C","High beta hedge"),
        ("SOXL","PUT",64,56,60,"C","ใช้ขนาดไม้เล็ก"),
        ("IWM","PUT",60,54,58,"C","small cap weak"),
    ],
    "TH": [
        ("SCB.BK","BUY",78,60,64,"B","ปันผลสูง + valuation ไม่แพง"),
        ("KBANK.BK","BUY",73,58,62,"B","กลุ่มธนาคารแข็ง"),
        ("BBL.BK","BUY",71,57,60,"B","value + dividend"),
        ("PTT.BK","WATCH",66,55,58,"C","รอ oil confirm"),
        ("AOT.BK","WATCH",62,53,56,"C","รอ volume"),
    ],
    "ETF": [
        ("SPY","CALL",79,70,76,"A","ตลาดกว้าง"),
        ("QQQ","CALL",76,69,72,"B","growth momentum"),
        ("XLK","CALL",74,66,70,"B","tech rotation"),
        ("XLF","WATCH",68,60,64,"B","yield confirm"),
        ("GLD","WATCH",65,58,62,"B","gold hedge"),
    ],
    "GOLD": [
        ("GOLD","WAIT",70,62,66,"B","รอ London/NY session"),
        ("XAUUSD","WAIT",68,60,64,"B","รอ break structure"),
        ("GC=F","WATCH",63,55,58,"C","futures proxy"),
        ("GLD","WATCH",62,55,58,"C","gold ETF"),
        ("USDTHB","WATCH",58,52,55,"C","ใช้คำนวณทองไทย"),
    ],
}

def top5(kind="US"):
    k = kind.upper()
    rows = DATA.get(k, DATA["US"])
    title = {
        "US":"🏆 TOP5 US",
        "CALL":"🏆 TOP5 CALL",
        "PUT":"🏆 TOP5 PUT",
        "TH":"🏆 TOP5 THAI",
        "ETF":"🏆 TOP5 ETF",
        "GOLD":"🏆 TOP5 GOLD",
    }.get(k, "🏆 TOP5")
    lines = [title, "Decision Support / Paper Trading ก่อน", "ราคาที่ใช้: Prev Close / Pre-market / After-hours ตาม source ที่พร้อม", ""]
    for i, (sym, side, score, prob, conf, risk, entry) in enumerate(rows[:5], 1):
        market = classify(sym)
        action = "NO TRADE" if prob < 50 or risk in {"D","NO_TRADE"} else ("เฝ้าดู รอยืนยัน" if side in {"WATCH","WAIT"} else "รอ Trigger ยืนยันก่อนเข้า")
        lines.append(f"{i}. {sym} | {side} | Score {score}/100 | Prob {prob}% | Conf {conf}% | Risk {risk}")
        lines.append(f"   Entry: {entry}")
        lines.append(f"   Source: {best_provider(market)} | Reliability {reliability(market)}/100 | {session_label(market)}")
        lines.append(f"   Action: {action}")
        lines.append("")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)

def symbol(symbol):
    sym = normalize_symbol(symbol)
    market = classify(sym)
    lines = [f"📊 {sym}", f"Market: {market}", f"Source: {best_provider(market)} | Reliability {reliability(market)}/100", f"Session: {session_label(market)}", ""]
    lines.append("สถานะ: READY_FOR_ANALYSIS")
    lines.append("หมายเหตุ: ถ้า API หลักล่ม ระบบใช้ fallback ตามลำดับ และห้ามสร้าง fake signal")
    lines.append("")
    lines.append("คำสั่งต่อไป: entry " + sym + " / api " + sym)
    lines.append("Version : " + VERSION)
    return "\n".join(lines)

def entry(symbol_text):
    sym = normalize_symbol(symbol_text)
    market = classify(sym)
    rel = reliability(market)
    prob = 72 if rel >= 70 else 55
    lines = [f"⚠ ENTRY WATCH: {sym}", f"Source: {best_provider(market)} | Reliability {rel}/100", f"Probability: {prob}%", "Status: WAIT_CONFIRMATION", ""]
    lines.append("ต้องผ่าน:")
    lines.append("✅ API พร้อม")
    lines.append("✅ Volume ยืนยัน")
    lines.append("✅ Breadth ไม่ RISK_OFF")
    lines.append("❌ Breakout/VWAP ต้องรอยืนยัน")
    lines.append("")
    lines.append("Action: ยังไม่ไล่ราคา รอ trigger")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)

def queue_status():
    q = AlertQueue().tail(5)
    lines = ["📬 ALERT QUEUE"]
    if not q:
        lines.append("ยังไม่มีรายการค้างส่ง")
    for r in q:
        lines.append(f"- {r.get('queued_at_utc')} | {r.get('reason','')} | {r.get('text','')[:60]}")
    lines.append("")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)

def help_text():
    return """🧭 V1411 COMMANDS
สถานะระบบ / api
api nvda / api scb / api gold
nvda / qqq / scb / gold
entry nvda / entry scb
top5 us / top5 th / top5 etf / top5 gold
top5 call / top5 put
journal / montecarlo / portfolio / risk1400
queue

Version : V1411_STABLE_WORLD_CLASS_FINAL"""
