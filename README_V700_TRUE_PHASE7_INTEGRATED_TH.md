# V700 TRUE PHASE 7 EXECUTION EDGE + V620 ALPHA DISCOVERY

สถานะ: ผสาน Phase 6 เป็นฐานและเพิ่ม Phase 7 เป็นชั้น Execution Edge จริง

## Endpoint หลัก
- `/v620/alpha-discovery`
- `/v620/alpha-discovery-json`
- `/v700/execution-edge`
- `/v700/execution-edge-json`
- `/v700/position-sizing`
- `/v700/kelly`
- `/v700/heat`
- `/v700/exposure`
- `/v700/correlation`
- `/v700/risk-control`

## หลักการ
Phase 7 ไม่ได้แยกเดี่ยว แต่ดึงผลจาก V620 Alpha Discovery มาแปลงเป็น grade, confidence, position sizing, Kelly, portfolio heat, exposure, correlation, concentration และ risk gate ก่อนส่งสัญญาณใช้งานจริง

## Safety
ระบบนี้ไม่รับประกันกำไร ใช้เพื่อช่วยวิเคราะห์และควบคุมความเสี่ยง ต้องมี Human Approval ก่อนส่งคำสั่งจริง
