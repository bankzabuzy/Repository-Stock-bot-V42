# V42.6 LINE US EXTENDED HOURS STABLE

เพิ่มให้ LINE Bot ตอบราคาหุ้นสหรัฐก่อนตลาดเปิด / หลังตลาดปิด / ช่วงตลาดปกติ

## คำสั่ง LINE
- `premarket`
- `afterhours`
- `หุ้นสหรัฐ`
- `nvda`
- `aapl`
- `tsla`
- `us nvda aapl tsla`

## Endpoint ทดสอบ
- `/v42/us-extended-hours`
- `/v42/us-extended-hours?symbols=NVDA,AAPL,TSLA`
- `/v42/us-extended-hours-line`
- `/v42/us-extended-hours-line?symbols=NVDA`

## ผลลัพธ์
แสดง:
- Session: Pre-Market / Regular / After Hours / Closed
- ราคา ณ ปัจจุบัน
- % เปลี่ยนแปลงเทียบ Previous Close
- ราคา Previous Close
