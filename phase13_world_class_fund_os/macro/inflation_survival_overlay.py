class InflationSurvivalOverlay:
    def evaluate(self, macro):
        cpi = float(macro.get("cpi_yoy", 2.5))
        real_yield = float(macro.get("real_yield", 0.5))
        usd = float(macro.get("usd_strength", 50))
        regime = "NORMAL"
        hedge_bias = []
        risk_add = 0
        if cpi > 3:
            regime = "INFLATION_DEFENSE"
            hedge_bias.extend(["GOLD", "QUALITY_STOCKS", "CASH_BUFFER"])
            risk_add += 10
        if real_yield > 1.5:
            hedge_bias.append("SHORT_DURATION")
            risk_add += 5
        if usd > 65:
            hedge_bias.append("USD_STRENGTH_FILTER")
            risk_add += 5
        return {"macro_regime": regime, "hedge_bias": hedge_bias, "macro_risk_add": risk_add}
