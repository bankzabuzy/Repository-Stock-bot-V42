# V1300.1.6.1 LINE FULL STOCK + EXTENDED HOURS

แก้ปัญหา V1300.1.6 ที่คำสั่งหุ้น เช่น `TSM`, `NVDA` ตอบเฉพาะ Extended Hours แล้วทำให้:
- จุดเข้าซื้อ
- Options
- Dividend / Valuation
- Technical report

ไม่แสดง

## พฤติกรรมใหม่
เมื่อพิมพ์ใน LINE:
- `tsm`
- `nvda`
- `aapl`

บอทจะตอบ:
1. รายงานหุ้นตัวเต็มจากระบบเดิม
2. ตามด้วย Extended Hours ปัจจุบัน เช่น Pre-Market / After Hours พร้อม % เปลี่ยนแปลง

คำสั่งรวมยังใช้ได้:
- `premarket`
- `afterhours`
- `หุ้นสหรัฐ`
- `us nvda aapl tsla`
