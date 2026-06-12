import math
import statistics

class RiskEngineV1400:
    """
    V1400 Risk Engine 2.0
    - Rule-based regime gating (VIX, breadth, confidence, news)
    - Kelly Criterion position sizing
    - Simplified VaR / CVaR estimation from trade history
    - Correlation penalty when same asset-class dominates
    """

    def evaluate(self, context):
        breadth    = float(context.get("breadth_score", 50) or 50)
        vix        = float(context.get("vix", 20) or 20)
        confidence = float(context.get("confidence", 50) or 50)
        news_risk  = float(context.get("news_risk", 30) or 30)
        high_impact = bool(context.get("high_impact_event", False))

        score = 100
        if breadth < 40:  score -= 20
        if vix > 25:      score -= 20
        if vix > 30:      score -= 30
        if confidence < 60: score -= 15
        if news_risk > 70:  score -= 20
        if high_impact:     score -= 20
        score = max(0, min(100, score))

        if score >= 80:
            grade, risk_pct, decision = "A", 0.010, "ALLOW"
        elif score >= 65:
            grade, risk_pct, decision = "B", 0.0075, "ALLOW_SMALL"
        elif score >= 50:
            grade, risk_pct, decision = "C", 0.005, "WATCH_ONLY"
        else:
            grade, risk_pct, decision = "NO_TRADE", 0.0, "BLOCK"

        return {
            "risk_score": round(score, 2),
            "grade": grade,
            "risk_pct": risk_pct,
            "decision": decision,
        }

    def kelly_fraction(self, win_rate, avg_win_r, avg_loss_r, max_fraction=0.25):
        """
        Kelly Criterion: f* = (p*b - q) / b
        where b = avg_win/avg_loss, p = win_rate, q = 1-p
        Capped at max_fraction (default 25% = half-Kelly at 0.125 is common practice).
        """
        try:
            p = float(win_rate)
            b = abs(float(avg_win_r)) / abs(float(avg_loss_r))
            q = 1.0 - p
            kelly = (p * b - q) / b
            kelly = max(0.0, min(max_fraction, kelly))
            return round(kelly, 4)
        except Exception:
            return 0.01

    def var_cvar(self, returns, confidence_level=0.95):
        """
        Historical VaR and CVaR (Expected Shortfall) from a list of returns.
        returns: list of floats (e.g. [-0.02, 0.01, 0.03, ...])
        """
        try:
            if not returns or len(returns) < 10:
                return {"var": None, "cvar": None, "note": "insufficient data (need >=10 returns)"}
            s = sorted(returns)
            idx = int(math.floor((1 - confidence_level) * len(s)))
            idx = max(0, idx)
            var = -s[idx]  # VaR is the loss (positive number)
            cvar = -statistics.mean(s[:idx + 1]) if idx >= 0 else var
            return {
                "var": round(var, 4),
                "cvar": round(cvar, 4),
                "confidence": confidence_level,
                "n": len(returns),
            }
        except Exception as e:
            return {"var": None, "cvar": None, "error": str(e)}

    def correlation_penalty(self, positions, threshold=0.60):
        """
        Simple heuristic: if more than threshold% of portfolio is same asset_type,
        reduce risk allowance by 20%.
        """
        try:
            if not positions:
                return 1.0
            counts = {}
            for p in positions:
                atype = p.get("asset_type", "UNKNOWN")
                counts[atype] = counts.get(atype, 0) + 1
            total = len(positions)
            max_concentration = max(counts.values()) / total
            if max_concentration > threshold:
                return 0.80  # 20% penalty
            return 1.0
        except Exception:
            return 1.0
