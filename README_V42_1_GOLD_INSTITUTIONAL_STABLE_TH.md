# V1300.1.1 GOLD INSTITUTIONAL STABLE

ปรับปรุงจาก V1300.1 เพื่อให้ Deploy บน Railway ได้เสถียรขึ้นและแก้ปัญหา `No module named modules.v42_gold_institutional_core` โดยจัดโครงสร้าง ZIP ให้ `main.py` และ `modules/` อยู่ที่ root ของโปรเจกต์โดยตรง

## Endpoint สำคัญ
- `/health`
- `/thai-gold`
- `/v42/gold`
- `/v42/gold-text`
- `/v41/top5`
- `/v41/top5-text`

## คำสั่ง LINE
- `gold`
- `ทอง`
- `ทองคำ`
- `xauusd`
- `top5`

## Gold Fallback
1. สมาคมค้าทองคำ / GoldTraders
2. ฮั่วเซ่งเฮง / Huasengheng
3. YLG Bullion
4. Estimate จาก XAUUSD × USDTHB

## Safety
- ถ้าแหล่งราคาทองล่ม ระบบไม่ crash
- endpoint คืนค่า HTTP 200 พร้อม `ok:false` หรือ fallback estimate
- Auto scan ข้าม error ราย symbol ได้
- ตรวจ `compileall` ผ่าน
