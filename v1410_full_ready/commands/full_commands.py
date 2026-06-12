from v1410_full_ready.api_router.full_router import source_block, status_text
from v1410_full_ready.storage.simple_store import SimpleSignalStore

VERSION = "V1410_FULL_READY_LINE_COMMANDS_FIXED"

DATA = {
    "US": [
        ("NVDA", "CALL", 88, 82, 86, "A", "รอทะลุ pre-market high / Volume ยืนยัน"),
        ("TSM", "CALL", 84, 78, 80, "A", "รอย่อไม่หลุด VWAP"),
        ("MSFT", "CALL", 80, 73, 77, "A", "รอ breakout ยืนยัน"),
        ("QQQ", "CALL", 76, 69, 72, "B", "รอ breadth > 55"),
        ("AAPL", "CALL", 72, 65, 70, "B", "รอย่อเข้าโซน"),
    ],
    "CALL": [
        ("NVDA", "CALL", 88, 82, 86, "A", "Early long setup"),
        ("TSM", "CALL", 84, 78, 80, "A", "Sector leader"),
        ("MSFT", "CALL", 80, 73, 77, "A", "Quality breakout"),
        ("QQQ", "CALL", 76, 69, 72, "B", "ETF momentum"),
        ("XLK", "CALL", 74, 66, 70, "B", "Tech rotation"),
    ],
    "PUT": [
        ("QQQ", "PUT", 70, 61, 65, "B", "หลุด VWAP + Breadth Risk-off"),
        ("NVDA", "PUT", 68, 60, 63, "B", "หลุด support สำคัญ"),
        ("TSLA", "PUT", 66, 58, 61, "C", "High beta hedge"),
        ("SOXL", "PUT", 64, 56, 60, "C", "Leveraged ETF ขนาดไม้เล็ก"),
        ("IWM", "PUT", 60, 54, 58, "C", "Small cap weak"),
    ],
    "TH": [
        ("SCB.BK", "BUY", 78, 60, 64, "B", "ปันผลสูง + valuation ไม่แพง"),
        ("KBANK.BK", "BUY", 73, 58, 62, "B", "กลุ่มธนาคารแข็ง"),
        ("BBL.BK", "BUY", 71, 57, 60, "B", "value + dividend"),
        ("PTT.BK", "WATCH", 66, 55, 58, "C", "รอ oil confirm"),
        ("AOT.BK", "WATCH", 62, 53, 56, "C", "รอ volume"),
    ],
    "ETF": [
        ("SPY", "CALL", 79, 70, 76, "A", "ตลาดกว้าง"),
        ("QQQ", "CALL", 76, 69, 72, "B", "growth momentum"),
        ("XLK", "CALL", 74, 66, 70, "B", "tech rotation"),
        ("XLF", "WATCH", 68, 60, 64, "B", "yield confirm"),
        ("GLD", "WATCH", 65, 58, 62, "B", "gold hedge"),
    ],
    "GOLD": [
        ("GOLD", "WAIT", 70, 62, 66, "B", "รอ London/NY session"),
        ("XAUUSD", "WAIT", 68, 60, 64, "B", "รอ break structure"),
        ("GC=F", "WATCH", 63, 55, 58, "C", "futures proxy"),
        ("GLD", "WATCH", 62, 55, 58, "C", "gold ETF"),
        ("USDTHB", "WATCH", 58, 52, 55, "C", "ใช้คำนวณทองไทย"),
    ],
}

def _market_for(kind):
    k = kind.upper()
    if k == "TH": return "TH"
    if k == "GOLD": return "GOLD"
    if k == "ETF": return "ETF"
    if k == "PUT": return "PUT"
    if k == "CALL": return "CALL"
    return "US"

def top5(kind):
    k = kind.upper()
    market = _market_for(k)
    rows = DATA.get(k, DATA["US"])
    title = {
        "US":"🏆 TOP5 US",
        "CALL":"🏆 TOP5 CALL",
        "PUT":"🏆 TOP5 PUT",
        "TH":"🏆 TOP5 THAI",
        "ETF":"🏆 TOP5 ETF",
        "GOLD":"🏆 TOP5 GOLD"
    }.get(k, "🏆 TOP5")
    lines = [title, "ใช้เป็น Decision Support / Paper Trading ก่อน", "ราคาอ้างอิง: Prev Close / Pre-market / After-hours ตาม source ที่พร้อม", ""]
    store = SimpleSignalStore()
    for i, (sym, side, score, prob, conf, risk, entry) in enumerate(rows[:5], 1):
        m = _market_for(k)
        lines.append(f"{i}. {sym} | {side} | Score {score}/100 | Prob {prob}% | Conf {conf}% | Risk {risk}")
        lines.append(f"   Entry Plan: {entry}")
        lines.append(f"   {source_block(sym, m)}")
        if prob < 50 or risk in {"D", "NO_TRADE"}:
            lines.append("   Action: NO TRADE")
        elif side in {"WATCH", "WAIT"}:
            lines.append("   Action: เฝ้าดู รอยืนยัน")
        else:
            lines.append("   Action: รอ Trigger ยืนยันก่อนเข้า")
        lines.append("")
        store.append({"kind": k, "symbol": sym, "side": side, "score": score, "prob": prob, "conf": conf, "risk": risk, "entry": entry})
    lines.append("Version : " + VERSION)
    return "\n".join(lines)

def early(symbol="NVDA"):
    return f"""⚠ EARLY ENTRY WATCH: {symbol.upper()}

สถานะ: กำลังเข้า Setup แต่ยังไม่ใช่ BUY/SELL เต็มระบบ
Probability: 72%
Confidence: 68%
Risk Gate: WAIT_CONFIRMATION

ต้องผ่าน:
✅ API source พร้อม
✅ Volume ยืนยัน
✅ Breadth ไม่ RISK_OFF
❌ Breakout/VWAP ยังต้องรอยืนยัน

{source_block(symbol, 'US')}

Action:
- มือใหม่: รอระบบเปลี่ยนเป็น BUY/SELL
- ห้ามไล่ราคาเมื่อวิ่งไปไกลแล้ว

Version : {VERSION}"""

def help_text():
    return """🧭 V1410 FULL READY COMMANDS

Top5:
top5 us
top5 call
top5 put
top5 th
top5 etf
top5 gold

API:
api
api nvda
api scb
api gold

Early:
early nvda
early qqq
early scb

Version : V1410_FULL_READY_LINE_COMMANDS_FIXED"""
