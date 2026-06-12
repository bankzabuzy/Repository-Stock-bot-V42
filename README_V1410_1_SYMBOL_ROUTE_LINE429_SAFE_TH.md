# V1410.1 SYMBOL ROUTE + LINE429 SAFE

## แก้จากภาพล่าสุด
1. พิมพ์ชื่อหุ้นเดี่ยว ๆ เช่น `scb`, `scb.bk`, `nvda`, `qqq`, `gold` จะไม่ตกไป handler เก่าแล้ว
2. ล้างข้อความ Version เก่า V1300/V1400/V1410 เดิมให้เป็น V1410.1
3. LINE push error 429 monthly limit จะไม่ทำให้ worker พัง

## สำคัญ
LINE error 429 = โควต้าส่ง Push รายเดือนหมด แก้ด้วยโค้ดไม่ได้ ต้องรอ reset หรืออัปเกรดแพ็กเกจ LINE
แต่คำสั่งแบบ Reply ที่พิมพ์ในแชตยังควรใช้งานได้ถ้าไม่ได้ชน quota ประเภทเดียวกัน

## หลัง deploy ให้ทดสอบ
- `v1410.1`
- `scb`
- `scb.bk`
- `nvda`
- `api nvda`
- `top5 us`

Version : V1410.1_SYMBOL_ROUTE_LINE429_SAFE
