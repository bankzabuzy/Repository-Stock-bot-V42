class WorldClassAlphaStack:
    def rank(self, symbols, market_snapshot, market_context, behavior, macro):
        scores = {}
        for s in symbols:
            d = market_snapshot.get(s, {})
            trend = float(d.get("trend_score", 50))
            momentum = float(d.get("momentum_score", trend))
            quality = float(d.get("quality_score", 55))
            liquidity = float(d.get("liquidity_score", 60))
            volatility = float(d.get("volatility_score", 50))
            behavioral = float(behavior.get("behavioral_score", 50))
            macro_penalty = float(macro.get("macro_risk_add", 0))
            score = trend*0.25 + momentum*0.20 + quality*0.15 + liquidity*0.15 + (100-volatility)*0.10 + behavioral*0.15 - macro_penalty
            if macro.get("macro_regime") == "INFLATION_DEFENSE" and s.upper() in {"GLD", "XAUUSD", "GOLD"}:
                score += 8
            if market_context.regime == "RISK_OFF" and volatility > 70:
                score -= 10
            scores[s] = round(max(0, min(100, score)), 2)
        return dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True))
