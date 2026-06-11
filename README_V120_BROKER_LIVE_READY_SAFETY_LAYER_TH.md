# V120 BROKER LIVE-READY SAFETY LAYER STABLE

ต่อจาก V110 โดยเพิ่ม Broker Layer แบบปลอดภัยและตรวจของเดิมด้วย compileall

## เพิ่มใหม่
- Broker Adapter Interface
- PAPER Broker ใช้งานได้ทันทีแบบจำลอง
- IBKR / Alpaca / MT5 / Binance เป็น stub-safe ยังไม่ยิงเงินจริง
- Pre-trade Risk Check
- Order Intent / Order Result Tables
- Order Router แบบ fail-safe
- Portfolio Snapshot รวมจากตารางเดิม
- Broker Center Dashboard

## Endpoints
- /v120/broker-center
- /v120/broker-center-json
- /v120/brokers
- /v120/order-test?symbol=SPY&side=BUY&qty=1&broker=PAPER&price=500
- /v120/portfolio

## LINE Commands
- v120
- broker
- broker center
- execution
- โบรกเกอร์
- ระบบส่งคำสั่ง

## Safety
LIVE trading ถูก block จนกว่าจะตั้ง:
ALLOW_LIVE_TRADING=true

แม้เลือก IBKR / Alpaca / MT5 / Binance ก็ยังเป็น stub-safe เพื่อป้องกันส่งคำสั่งเงินจริงโดยไม่ตั้งใจ
