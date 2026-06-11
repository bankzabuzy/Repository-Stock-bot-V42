# V550 PHASE 5 WEBULL API READY SAFE EXECUTION STABLE

ต่อจาก V500 โดยเพิ่ม Phase 5 เพื่อเตรียมเชื่อมต่อ Webull OpenAPI แบบปลอดภัย

## V510 Broker Integration Layer
- Webull
- Alpaca
- IBKR
- MT5
- Binance
- PAPER
- Broker status / safe mode

## V520 Secret Manager
- WEBULL_API_KEY
- WEBULL_SECRET_KEY
- WEBULL_ACCOUNT_ID
- LINE_CHANNEL_ACCESS_TOKEN
- ADMIN_TOKEN
- Masked audit
- No hardcode policy

## V530 Order Simulator + Dry Run
- slippage
- commission
- notional cap
- no real order

## V540 Human Approval Center
- SAFE
- SEMI_AUTO
- FULL_AUTO policy stub
- approval queue

## V550 API Health Center
- Webull API status
- token status
- latency
- reconnect action
- safety center
- duplicate order protection
- kill switch foundation

## Endpoints
- /v550/phase5-center
- /v550/secrets
- /v550/brokers
- /v550/dry-run
- /v550/approval
- /v550/api-health
- /v550/safety

## LINE Commands
- v550
- phase5
- webull api
- webull ready
- api health
- human approval
- dry run
- เชื่อม webull
- ตรวจ api

## .env ที่ต้องตั้งหลัง Webull อนุมัติ
WEBULL_API_KEY=...
WEBULL_SECRET_KEY=...
WEBULL_ACCOUNT_ID=...
LINE_CHANNEL_ACCESS_TOKEN=...
ADMIN_TOKEN=...

## Safety
ยังไม่ส่งคำสั่งจริง จนกว่า:
1. Webull อนุมัติ API
2. ตั้งค่า .env ครบ
3. ผ่าน dry-run
4. Human approval
5. Broker adapter final validation
