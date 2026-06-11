# V1300.1 WORLD CLASS FINAL

ฐานเดิมล่าสุดถูกเก็บไว้ครบ `main.py` ยังมี 13408 บรรทัด

## แก้ไขแล้ว
- DATA_UNAVAILABLE ไม่แสดง RSI=100 แล้ว แสดง RSI=N/A
- ปิดแผนเข้าเมื่อ Probability < 50
- ซ่อน CALL ถ้า Timeframe เป็น BEARISH ทุกตัว
- เพิ่ม Market Breadth
- เพิ่ม DXY + Yield
- เพิ่ม Earnings Calendar
- เพิ่ม Sector Rotation
- เพิ่ม Ticker Mapping Guard
- เปลี่ยนข้อความเวอร์ชันที่ผู้ใช้เห็นเป็น `Version : V1300.1_WORLD_CLASS_FINAL`

## Railway Start Command
```bash
gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --threads 4
```
