# V1410 MASTER OS ENHANCED

ต่อยอดจาก V1410_DEDUP_FIXED แบบ additive

## คำสั่ง LINE ใหม่
- `top5 us`
- `top5 call`
- `top5 put`
- `top5 th`
- `top5 etf`
- `top5 gold`
- `api`
- `api nvda`
- `api scb`
- `api gold`
- `early nvda`
- `v1410`

## Routes ใหม่
- `/v1410/top5/us`
- `/v1410/top5/call`
- `/v1410/top5/put`
- `/v1410/top5/th`
- `/v1410/top5/etf`
- `/v1410/top5/gold`
- `/v1410/api`
- `/v1410/api/NVDA`
- `/v1410/early/NVDA`

## API Priority
US/ETF: Webull > Polygon > Finnhub > TwelveData > AlphaVantage > Yahoo
Options: Webull > Polygon > Yahoo
Thai: SET API > Thai Market API > Yahoo .BK
Gold: GoldTraders > GoldAPI > XAUUSD TwelveData > GC=F Yahoo
Macro: FRED > AlphaVantage > Yahoo

## หมายเหตุ
เป็น Decision Support / Paper Trading ก่อน ไม่รับประกันกำไร
ระบบจะใช้ NO TRADE เมื่อความน่าจะเป็นต่ำหรือข้อมูลไม่พร้อม

Version : V1410_MASTER_OS_ENHANCED
