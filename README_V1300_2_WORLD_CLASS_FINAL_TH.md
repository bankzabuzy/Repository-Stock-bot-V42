# V1300.2 WORLD CLASS FINAL VERIFIED

## สิ่งที่เพิ่ม
- เพิ่ม Market Session ในข้อความ LINE
- เพิ่ม Price Source ใน Top5 และรายงานรายตัว
- กติกา Top5:
  - ตลาดปิด = PREV_CLOSE
  - ก่อนเปิดตลาด = PREMARKET เมื่อมีข้อมูล
  - ตลาดเปิด = REGULAR_SESSION
  - หลังตลาดปิด = AFTER_HOURS
  - หุ้นไทย = SET_LAST_CLOSE
- บังคับ Version แสดงเป็น V1300.2_WORLD_CLASS_FINAL
- แก้ World Context ที่เคยมี `\n` ให้ขึ้นบรรทัดจริง

## ทดสอบหลัง Deploy
พิมพ์ใน LINE:
- สถานะระบบ
- top5
- nvda
- qqq
- scb

ควรเห็นบรรทัด:
Market Session: ...
Price Source: ...
Version : V1300.2_WORLD_CLASS_FINAL
