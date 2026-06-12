# V1410 FULL READY LINE COMMANDS FIXED

เวอร์ชันนี้เป็นโค้ดเต็มสำหรับวางทับระบบเดิมได้เลย ไม่ใช่ตัวอย่าง

## แก้ปัญหา
- ไม่พึ่งตัวแปร `v1300_4_prev_filter` อีก
- เพิ่ม LINE commands เต็ม:
  - top5 us
  - top5 call
  - top5 put
  - top5 th
  - top5 etf
  - top5 gold
  - api
  - api nvda
  - api scb
  - api gold
  - early nvda
- รองรับ Webull API priority ในอนาคต
- เก็บ snapshot สัญญาณเป็น JSONL `v1410_signals.jsonl`

## Routes
- /v1410/full/top5/us
- /v1410/full/top5/call
- /v1410/full/top5/put
- /v1410/full/top5/th
- /v1410/full/top5/etf
- /v1410/full/top5/gold
- /v1410/full/api
- /v1410/full/api/NVDA
- /v1410/full/early/NVDA

Version : V1410_FULL_READY_LINE_COMMANDS_FIXED
