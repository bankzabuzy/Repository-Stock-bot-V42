# V1414 REALTIME PRICE ROUTER FINAL

แก้จากฐาน V1413 ให้ระบบใช้ราคาปัจจุบันที่สุดก่อนเสมอ:
- US/ETF: Polygon snapshot/last trade > Finnhub > TwelveData > Yahoo includePrePost > fallback
- หุ้นไทย: Yahoo .BK chart > fallback
- ทอง: สมาคมค้าทองคำเป็นหลัก > GoldAPI > XAUUSD > GC=F > fallback

เพิ่มใน LINE:
- Price Mode: LIVE / PREMARKET / AFTERHOURS / LAST_CLOSE / FALLBACK
- Price Source
- เวลาอัปเดตราคา
- แจ้งเตือนถ้าข้อมูลอาจล่าช้า
- ยังรักษา V1413: คาดการณ์ 1–3 วัน, 3 ไม้, TP/SL, Options, Volume, Dividend, P/E

คำสั่ง:
nvda
qqq
scb
gold
top5 us
api nvda

Routes:
GET /v1414/full/NVDA
GET /v1414/price/NVDA
GET /v1414/health

Version : V1414_REALTIME_PRICE_ROUTER_FINAL
