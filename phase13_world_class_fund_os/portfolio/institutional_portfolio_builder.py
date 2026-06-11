class InstitutionalPortfolioBuilder:
    def build(self, alpha_scores, max_positions=5):
        selected = list(alpha_scores.items())[:max_positions]
        if not selected:
            return {"selected": [], "weights": {}}
        raw = {sym: max(score, 1) for sym, score in selected}
        total = sum(raw.values()) or 1
        weights = {sym: round(v/total, 4) for sym, v in raw.items()}
        return {"selected": list(weights.keys()), "weights": weights}
