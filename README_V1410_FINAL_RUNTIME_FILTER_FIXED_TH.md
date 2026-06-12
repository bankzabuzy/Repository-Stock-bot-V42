# V1410 FINAL RUNTIME FILTER FIXED

แก้ปัญหาจาก Railway log:

`NameError: name '_v1300_4_prev_filter' is not defined`

## สิ่งที่แก้
- เพิ่ม `_v1300_4_prev_filter` ก่อนจุดที่ wrapper รุ่นเก่าเรียกใช้งาน
- เปลี่ยน `v1300_1_force_filter_before_line_send()` ให้ใช้ globals safe lookup
- เพิ่ม safe defaults สำหรับ auto scan worker
- คงคำสั่ง LINE:
  - top5 us
  - top5 call
  - top5 put
  - top5 th
  - top5 etf
  - top5 gold
  - api nvda
  - early nvda

## หลัง Deploy ให้ทดสอบใน LINE
1. `top5 us`
2. `top5 call`
3. `api nvda`
4. `early nvda`

Version : V1410_FINAL_RUNTIME_FILTER_FIXED
