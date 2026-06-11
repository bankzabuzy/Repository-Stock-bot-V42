# V40 FIXED DEPLOY PACKAGE

แพ็กเกจนี้แก้ปัญหา Railway log:

`No module named modules.v35_institutional_free_core`

โดยรวมไฟล์ฐานที่จำเป็นครบ:

- modules/v35_institutional_free_core.py
- modules/v35_institutional_free_routes.py
- modules/v36_institutional_free_core.py
- modules/v36_institutional_free_routes.py
- modules/v37_live_safety_broker_ready_core.py
- modules/v37_live_safety_broker_ready_routes.py
- modules/v38_institutional_free_core.py
- modules/v38_institutional_free_routes.py
- modules/v39_validation_paper_broker_proof_core.py
- modules/v39_validation_paper_broker_proof_routes.py
- modules/v40_adaptive_multi_agent_core.py
- modules/v40_adaptive_multi_agent_routes.py

วิธีลง: แตก ZIP แล้วลากไฟล์ทั้งหมดในโฟลเดอร์ stockbot ขึ้น GitHub ทับของเดิม จากนั้น Commit และ Redeploy ใน Railway

ตรวจสอบหลัง Deploy:

- /health
- /dashboard
- /v36/health
- /v37/health
- /v38/health
- /v39/health
- /v40/dashboard
- /v40/report
