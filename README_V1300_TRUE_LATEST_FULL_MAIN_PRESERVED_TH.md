# V1300 Phase 13 TRUE LATEST – Full Main Preserved

ฐานที่ใช้: V1200 Phase 12 LivePrice

## สิ่งสำคัญที่สุด
ไฟล์ `main.py` เดิมที่มี 13,245 บรรทัดถูกเก็บไว้ ไม่ถูกแทนที่ด้วย main.py แบบย่อ

## สิ่งที่เพิ่ม
- Phase 13 World-Class Fund OS แบบ additive module
- Behavioral Crowd Engine
- Inflation / Macro Overlay
- World-Class Alpha Stack
- Institutional Portfolio Builder
- Fund-Grade Risk Engine
- Immutable Audit V13
- Version Guard ตรวจว่า main.py ยังไม่ถูกตัดสั้น
- CLI: `python run_phase13_current.py`

## Railway
ใช้ Start Command เดิม:
```bash
gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --threads 4
```

## การตรวจสอบ
```bash
python run_phase13_current.py
python -m compileall .
python -m pytest phase13_world_class_fund_os/tests -q
```

ระบบนี้ไม่รับประกันกำไร เป้าหมายคือช่วยตัดสินใจ ควบคุมความเสี่ยง และทดสอบ forward test อย่างมีวินัย
