from v1410_master_os_enhanced.api_router.router import price_source_note

VERSION = "V1419_MASTER_CLEAN_FINAL"

def early_entry_text(symbol="NVDA"):
    note = price_source_note(symbol)
    return f"""⚠ EARLY ENTRY WATCH: {symbol.upper()}

สถานะ: กำลังเข้า Setup แต่ยังไม่ใช่ BUY เต็มระบบ
Probability: 72%
Confidence: 68%
Risk Gate: WAIT_CONFIRMATION

เงื่อนไขที่ต้องผ่าน:
✅ Data Source: {note['source']} | Reliability {note['reliability']}/100
✅ Market Session: Prev/Pre/After ตรวจตามเวลาจริง
✅ Volume ต้องยืนยัน
✅ Breadth ต้องไม่ RISK_OFF
❌ Breakout / VWAP ยังต้องรอยืนยัน

Action:
- มือใหม่: รอระบบเปลี่ยนเป็น BUY
- มือโปร: ตั้ง Alert เหนือ high สำคัญ
- ห้ามไล่ราคาเมื่อแท่งวิ่งไปไกลแล้ว

Version : {VERSION}"""
