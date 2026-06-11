# V1300.1 LINE REPLY FILTERED FINAL

รอบนี้แก้จุดที่หลุดจริง: `line_reply()` และ `line_push()`

## สิ่งที่แก้
- ทุกข้อความก่อนออก LINE จะถูกกรองด้วย `v1300_1_force_filter_before_line_send()`
- ถ้ามี `DATA_UNAVAILABLE` + `📊 วิเคราะห์` จะไม่ส่ง AI Score/RSI/Entry ปลอม
- จะส่งเฉพาะ `NO ANALYSIS / NO TRADE`
- บังคับ Version เป็น `V1300.1_WORLD_CLASS_FINAL`

## หลัง Deploy ให้ทดสอบ
พิมพ์ใน LINE:
- `สถานะ`
- `nvda`
- `scb`

ถ้าข้อมูล API ล้ม ต้องเห็นข้อความสั้น `NO ANALYSIS / NO TRADE`
ห้ามเห็น AI Score 50/100, RSI หรือแผนเข้าไม้ปลอมอีก
