# V1300.1.4 GOLD INSTITUTIONAL FUND GRADE STABLE

ต่อยอดจาก V1300.1.3 โดยเพิ่ม:
- Economic Calendar Filter: CPI / FOMC / NFP / Powell Speech
- DXY + Bond Yield Filter: DXY ขึ้น + Yield ขึ้น ลดคะแนนฝั่ง Buy ทอง
- Order Block Detection: Demand Zone / Supply Zone
- Liquidity Sweep Detection: Stop Hunt / Fake Breakout
- Winrate Dashboard: Win %, Profit Factor, Max Drawdown, Average RR
- Self Learning: จำผลจริงและปรับคะแนนแบบอนุรักษ์นิยม
- Endpoint ใหม่: /v42/gold-fund-grade และ /v42/gold-dashboard

Railway ENV ที่แนะนำ:
- HIGH_IMPACT_NEWS_ACTIVE=false
- HIGH_IMPACT_NEWS_EVENT=CPI/FOMC/NFP/Powell
- HIGH_IMPACT_NEWS_WINDOW_MIN=30
- V1300.1_ECON_EVENT_TIME_UTC=
- V1300.1_DXY_TREND=
- V1300.1_US10Y_TREND=
- V1300.1_MACRO_BUY_PENALTY=8
- V1300.1_SELF_LEARNING_MIN_TRADES=30
