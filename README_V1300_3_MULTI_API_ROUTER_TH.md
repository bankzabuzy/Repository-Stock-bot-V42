# V1300.3 MULTI API ROUTER + REAL HEALTH STATUS

แก้ตามคำขอ:
- ระบบจัดลำดับ API ตามความน่าเชื่อถือ
- มีสถานะ API จริงว่า key ไหนตั้งค่าแล้ว / ไม่ได้ตั้งค่า
- หุ้นไทยมี Router: SET official/partner > Thai provider > Yahoo .BK > fallback
- ทองมี Router: GoldTraders/สมาคมค้าทองคำ > Gold API > XAUUSD × USDTHB > GC=F fallback
- US/ETF มี Router: Polygon > Finnhub > TwelveData > AlphaVantage > Yahoo
- LINE มีคำสั่งตรวจสถานะ API

## คำสั่ง LINE
- `สถานะระบบ`
- `api`
- `สถานะ SCB`
- `สถานะ SCB.BK`
- `สถานะ GOLD`
- `api NVDA`

## Endpoint
- `/v1300_3/api-health`
- `/v1300_3/api-health.txt`
- `/v1300_3/symbol-status/NVDA`
- `/v1300_3/symbol-status/SCB.BK`
- `/v1300_3/symbol-status/GOLD`

## ตัวแปร Railway ที่แนะนำ
- `POLYGON_API_KEY` สำหรับหุ้น US/ETF คุณภาพสูง
- `FINNHUB_API_KEY` สำหรับ quote/news
- `TWELVEDATA_API_KEY` สำหรับ time series/XAUUSD
- `ALPHAVANTAGE_API_KEY` สำหรับ fallback
- `SET_API_KEY` หรือ `THAI_MARKET_API_KEY` สำหรับหุ้นไทยแบบจริงจัง
- `GOLD_API_KEY` สำหรับ XAUUSD/Gold fallback
- `FRED_API_KEY` หรือ `TRADINGECONOMICS_API_KEY` สำหรับ macro

Version : V1300.3_MULTI_API_ROUTER_GOLD_THAI_READY
