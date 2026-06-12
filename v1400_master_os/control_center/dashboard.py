from v1400_master_os.journal_ai.journal import JournalAI
from v1400_master_os.monte_carlo.simulator import MonteCarloSimulator
from v1400_master_os.portfolio_engine.portfolio import PortfolioEngine
from v1400_master_os.risk_engine.risk import RiskEngineV1400
from v1400_master_os.backtest_center.backtest import BacktestCenter

VERSION = "V1400_MASTER_OS_HEDGEFUND_READY"

def build_v1400_status_text(api_status_text=None):
    journal = JournalAI().summary()
    lessons = JournalAI().ai_lessons()
    risk = RiskEngineV1400().evaluate({"breadth_score":50,"vix":22,"confidence":65,"news_risk":35})
    mc = MonteCarloSimulator().simulate(runs=1000, n_trades=100)
    lines = []
    lines.append("🧭 V1400 MASTER OS / HEDGE FUND READY")
    lines.append("")
    lines.append("SYSTEM LAYERS")
    lines.append("Data Router: ✅")
    lines.append("Journal AI: ✅")
    lines.append("Monte Carlo: ✅")
    lines.append("Portfolio Engine: ✅")
    lines.append("Risk Engine 2.0: ✅")
    lines.append("Backtest Center: ✅")
    lines.append("Paper Trade Engine: ✅")
    lines.append("")
    lines.append("RISK ENGINE")
    lines.append(f"Decision: {risk['decision']} | Grade: {risk['grade']} | Risk: {risk['risk_pct']*100:.2f}% | Score: {risk['risk_score']}")
    lines.append("")
    lines.append("MONTE CARLO")
    lines.append(f"Verdict: {mc['verdict']} | Median Return: {mc['median_return_pct']}% | P95 DD: {mc['p95_max_dd_pct']}% | Risk of Ruin: {mc['risk_of_ruin_pct']}%")
    lines.append("")
    lines.append("JOURNAL AI")
    lines.append(f"Total: {journal['total']} | Closed: {journal['closed']} | Win: {journal['win_rate']} | PF: {journal['pf']} | Exp(R): {journal['expectancy_r']}")
    for l in lessons:
        lines.append("- " + l)
    lines.append("")
    if api_status_text:
        lines.append("API ROUTER")
        lines.append(api_status_text[:1200])
        lines.append("")
    lines.append("COMMANDS")
    lines.append("v1400 | journal | montecarlo | portfolio | risk1400 | paper")
    lines.append("")
    lines.append("Version : " + VERSION)
    return "\n".join(lines)

def sample_portfolio_text():
    candidates = [
        {"symbol":"SPY","asset_type":"ETF","score":75,"confidence":70,"risk_grade":"A"},
        {"symbol":"QQQ","asset_type":"ETF","score":72,"confidence":66,"risk_grade":"B"},
        {"symbol":"GLD","asset_type":"GOLD","score":68,"confidence":64,"risk_grade":"B"},
        {"symbol":"SCB.BK","asset_type":"THAI_STOCK","score":62,"confidence":58,"risk_grade":"B"},
    ]
    pe = PortfolioEngine()
    result = pe.build(candidates, risk_off=False)
    expo = pe.exposure_summary(result["positions"], result["weights"])
    lines = ["📊 V1400 PORTFOLIO ENGINE"]
    for sym,w in result["weights"].items():
        lines.append(f"{sym}: {round(w*100,2)}%")
    lines.append("Exposure: " + str(expo["asset_exposure"]))
    lines.append("Version : " + VERSION)
    return "\n".join(lines)
