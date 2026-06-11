
# V1300 Phase 13 World Class Fund OS - TRUE LATEST

เวอร์ชันนี้สร้างใหม่เพื่อแก้ปัญหา deploy แล้วยังเห็น V42.8 โดยตรง:

- `main.py` ถูกแทนที่เป็น V1300 entrypoint ใหม่
- `/`, `/health`, `/version`, `/v13`, `/v13/top5`, `/v13/risk`, `/v13/audit` แสดง V1300
- `/v42` เป็น compatibility route แต่ตอบว่า legacy ถูกอัปเกรดเป็น V1300 แล้ว
- เพิ่มโมดูล `v800` ถึง `v1300` ใน `modules/`
- เพิ่ม `phase13_world_class_fund_os/` สำหรับ scoring, behavioral alpha, risk, audit
- Safety default: `LIVE_TRADING_ENABLED=false`, `HUMAN_APPROVAL_REQUIRED=true`

## Railway Start Command

```bash
gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --threads 4
```

## เช็กว่าเป็นเวอร์ชันใหม่จริง

เปิด URL:

```text
/health
/version
/v13
/v13/top5
/v42
```

ทุกหน้าต้องเห็น `V1300_PHASE13_WORLD_CLASS_FUND_OS_TRUE_LATEST`

## รันทดสอบในเครื่อง

```bash
python run_phase13_current.py
python -m compileall .
```

หมายเหตุ: ระบบนี้เป็น Decision Support / Paper Trading ก่อน ไม่รับประกันกำไร และ Live trading ถูกปิดเป็นค่าเริ่มต้น
