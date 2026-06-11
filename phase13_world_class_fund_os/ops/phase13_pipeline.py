import json
from pathlib import Path
from phase13_world_class_fund_os.market.market_context import MarketContextEngine
from phase13_world_class_fund_os.behavioral.crowd_behavior_engine import CrowdBehaviorEngine
from phase13_world_class_fund_os.macro.inflation_survival_overlay import InflationSurvivalOverlay
from phase13_world_class_fund_os.alpha.world_class_alpha_stack import WorldClassAlphaStack
from phase13_world_class_fund_os.portfolio.institutional_portfolio_builder import InstitutionalPortfolioBuilder
from phase13_world_class_fund_os.risk.fund_grade_risk_engine import FundGradeRiskEngine
from phase13_world_class_fund_os.execution.decision_support import DecisionSupportFormatter
from phase13_world_class_fund_os.governance.immutable_audit_v13 import ImmutableAuditV13

class Phase13Pipeline:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).resolve().parents[1] / "config" / "phase13_config.json"
        self.config = json.loads(Path(config_path).read_text(encoding="utf-8"))
        self.market = MarketContextEngine()
        self.behavior = CrowdBehaviorEngine()
        self.macro = InflationSurvivalOverlay()
        self.alpha = WorldClassAlphaStack()
        self.portfolio = InstitutionalPortfolioBuilder()
        self.risk = FundGradeRiskEngine(self.config.get("risk_limits", {}))
        self.formatter = DecisionSupportFormatter()
        self.audit = ImmutableAuditV13()

    def run(self, symbols, snapshot, market_data, sentiment, macro_input, account):
        market_context = self.market.evaluate(market_data)
        behavior = self.behavior.score(sentiment)
        macro = self.macro.evaluate(macro_input)
        alpha_scores = self.alpha.rank(symbols, snapshot, market_context, behavior, macro)
        portfolio = self.portfolio.build(alpha_scores)
        risk = self.risk.check(portfolio, account, market_context, behavior)
        message = self.formatter.format_top5(alpha_scores, portfolio, risk)
        audit = self.audit.log("phase13_decision", {
            "symbols": symbols, "market_context": market_context.__dict__, "behavior": behavior,
            "macro": macro, "alpha_scores": alpha_scores, "portfolio": portfolio, "risk": risk
        })
        return {
            "version": "V1300_PHASE13_TRUE_LATEST_FULL_MAIN_PRESERVED",
            "base": "V1200_LIVEPRICE_FULL_MAIN",
            "market_context": market_context.__dict__,
            "behavior": behavior,
            "macro": macro,
            "alpha_scores": alpha_scores,
            "portfolio": portfolio,
            "risk": risk,
            "message": message,
            "audit_hash": audit["hash"],
            "audit_verified": self.audit.verify()
        }
