# V1300.1.3 GOLD INSTITUTIONAL HIGH CONVICTION STABLE

ต่อยอดจาก V1300.1.2 โดยเพิ่มโค้ดใช้งานจริง:

- Entry Score Engine
- Session Filter: London / New York
- High Impact News Filter: FOMC / CPI / NFP / Powell ผ่าน ENV
- Spread Filter
- Smart Trailing Stop: TP1 → BE, TP2 → Lock Profit, TP3 → Close
- STRONG BUY Engine
- High Conviction LINE Push
- Endpoint ใหม่ `/v42/gold-high-conviction`
- ป้องกัน route ซ้ำ `/v42/gold-filter`

## ENV เสริม

- `V1300.1_ALLOW_ALL_SESSIONS=true` ถ้าต้องการให้ทดสอบแจ้งเตือนได้ทุก session
- `HIGH_IMPACT_NEWS_ACTIVE=true` เมื่อต้องการหยุดก่อนข่าวแรง
- `HIGH_IMPACT_NEWS_EVENT=FOMC/CPI/NFP/Powell`
- `HIGH_IMPACT_NEWS_WINDOW_MIN=30`
- `GOLD_MAX_THAI_SPREAD=450`
- `GOLD_CURRENT_XAU_SPREAD=0`
- `GOLD_MAX_XAU_SPREAD=5`

## Test URLs

- `/v42/gold`
- `/v42/gold-text`
- `/v42/gold-filter`
- `/v42/gold-high-conviction`
- `/thai-gold`

