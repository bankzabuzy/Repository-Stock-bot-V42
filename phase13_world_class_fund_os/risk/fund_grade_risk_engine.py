class FundGradeRiskEngine:
    def __init__(self, limits=None):
        self.limits = limits or {}
    def check(self, portfolio, account, market_context, behavior):
        blocks, warnings = [], []
        if float(account.get("daily_loss_pct", 0)) >= self.limits.get("max_daily_loss_pct", 0.02):
            blocks.append("daily_loss_limit")
        if float(account.get("drawdown_pct", 0)) >= self.limits.get("max_drawdown_pause_pct", 0.08):
            blocks.append("max_drawdown_pause")
        if market_context.regime == "RISK_OFF":
            warnings.append("risk_off_reduce_size")
        warnings.extend(behavior.get("warnings", []))
        for sym, w in portfolio.get("weights", {}).items():
            if w > self.limits.get("max_position_pct_equity", 0.04) * 3:
                warnings.append(f"concentration_review:{sym}")
        return {"allowed": len(blocks)==0, "blocks": blocks, "warnings": warnings}
