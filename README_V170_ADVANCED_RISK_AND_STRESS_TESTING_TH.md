# V170 ADVANCED RISK AND STRESS TESTING STABLE

ต่อจาก V160 โดยเพิ่ม Advanced Risk & Stress Testing แบบไม่กระทบ Production

## เพิ่มใหม่
- Monte Carlo Stress Test
- Historical Crash Replay / Scenario Engine
  - COVID Crash
  - 2008 Crisis
  - Inflation Shock
  - AI Bubble Burst
  - USD Spike
- Portfolio VaR / CVaR
- Correlation Matrix
- Concentration Risk
- Tail Risk Detector
- Liquidity Risk
- Drawdown Recovery Analysis
- Risk Heatmap
- Stress Dashboard
- DB table: v170_stress_runs, v170_risk_events

## Endpoints
- /v170/risk-center
- /v170/risk-center-json
- /v170/scenarios
- /v170/monte-carlo
- /v170/var-cvar
- /v170/correlation

## LINE Commands
- v170
- stress
- risk stress
- stress test
- var
- cvar
- ทดสอบความเสี่ยง
- ความเสี่ยงขั้นสูง
