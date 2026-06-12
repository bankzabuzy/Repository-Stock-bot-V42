# V1411 STABLE WORLD CLASS FINAL

เวอร์ชันนี้แก้จากฐานเดิมและรวมเป้าหมายทั้งหมดที่คุยกัน:
- ใช้ Version ล่าสุดเดียว
- LINE command หลักกลับมาใช้งาน
- API Router ตามลำดับความแม่นยำ
- Symbol route เช่น nvda / scb / gold
- Entry watch
- Top5 us/th/etf/gold/call/put
- LINE 429 queue ไม่ให้ worker พัง
- No fake signal principle

## คำสั่ง LINE ที่ต้องทดสอบหลัง Deploy
- `สถานะระบบ`
- `api`
- `api nvda`
- `nvda`
- `scb`
- `gold`
- `entry nvda`
- `top5 us`
- `top5 call`
- `top5 put`
- `top5 th`
- `top5 etf`
- `top5 gold`
- `queue`

## Routes
- `/v1411/status`
- `/v1411/top5/us`
- `/v1411/top5/call`
- `/v1411/top5/put`
- `/v1411/top5/th`
- `/v1411/top5/etf`
- `/v1411/top5/gold`
- `/v1411/symbol/NVDA`
- `/v1411/symbol/SCB`

## สำคัญ
ถ้า LINE ขึ้น 429 monthly limit = โควต้า LINE หมด แก้ด้วยโค้ดไม่ได้ แต่ระบบนี้จะ queue alert และไม่ให้ worker ล้ม

Version : V1411_STABLE_WORLD_CLASS_FINAL
