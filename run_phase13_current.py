
from phase13_world_class_fund_os.version import VERSION
from phase13_world_class_fund_os.market_intelligence import top_signals, market_breadth
from phase13_world_class_fund_os.risk_engine import portfolio_heat, position_size, safety_status
from phase13_world_class_fund_os.behavioral_alpha import crowd_psychology_overlay, market_reflexivity_check

symbols = ["GLD","NVDA","AAPL","TSLA","QQQ","SPY","AMD","META"]
print(f"V13 TRUE LATEST CHECK: {VERSION}")
print("MARKET BREADTH:", market_breadth(symbols))
rows=top_signals(symbols,5)
for i,r in enumerate(rows,1):
    print(f"{i}. {r['symbol']} | {r['signal']} | Score={r['score']} | Risk={r['risk']} | Position={position_size(r)['risk_pct']*100:.1f}% | {crowd_psychology_overlay(r)['behavior_action']}")
print("PORTFOLIO HEAT:", portfolio_heat(rows))
print("SAFETY:", safety_status(False, True))
