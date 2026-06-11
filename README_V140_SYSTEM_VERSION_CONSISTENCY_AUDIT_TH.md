# V140 SYSTEM VERSION CONSISTENCY AUDIT STABLE

ต่อจาก V130 โดยเพิ่มชั้นตรวจสอบว่าโปรเจกต์รันเป็นเวอร์ชันล่าสุดจริง

## เพิ่มใหม่
- Version Registry
- Version Consistency Audit
- Route Registry
- Latest System Center
- Audit DB table: v140_version_audit
- LINE คำสั่งตรวจเวอร์ชัน

## Endpoints
- /v140/system-center
- /v140/system-center-json
- /v140/version-audit
- /v140/routes

## LINE Commands
- v140
- latest
- version
- system center
- ตรวจเวอร์ชั่น
- เวอร์ชั่นล่าสุด

## หมายเหตุสำคัญ
ระบบยังเก็บ V1300.1-V130 ไว้เพื่อ backward compatibility
ดังนั้นการเห็นชื่อเวอร์ชันเก่าในโมดูลเก่าไม่ใช่ความผิดพลาด
แต่หน้า System Center ล่าสุดต้องแสดง V140 เป็น latest control layer
