# V130 LIVE TRADING READINESS & AUTONOMOUS PORTFOLIO CONTROL STABLE

ต่อจาก V120 โดยตรวจของเดิมและเพิ่มชั้น Governance + Allocation + Autonomous Control แบบปลอดภัย

## เพิ่มใหม่
- Live Trading Readiness Checklist
- Broker Layer Health Check เชื่อมกับ V120
- Fund Platform Check เชื่อมกับ V110
- Capital Allocation Engine
- Rebalance Intent Generator
- Autonomous Mode แบบ Paper-first
- Incident Log / Incident Summary
- Governance Center Dashboard

## Endpoints
- /v130/governance-center
- /v130/governance-json
- /v130/readiness
- /v130/allocation
- /v130/autonomous-rebalance
- /v130/incidents

## LINE Commands
- v130
- governance
- readiness
- allocation
- autonomous
- บริหารพอร์ต
- พร้อมใช้งานจริง

## Safety
ยังไม่ส่งคำสั่งเงินจริงอัตโนมัติ
LIVE trading ถูก block จนกว่าจะตั้ง ALLOW_LIVE_TRADING=true
Autonomous rebalance สร้างเป็น intent รออนุมัติ ไม่ยิง order จริงทันที
