import math

class PortfolioEngine:
    def normalize(self, scores):
        total = sum(max(0, float(v)) for v in scores.values()) or 1
        return {k: round(max(0,float(v))/total,4) for k,v in scores.items()}

    def build(self, candidates, max_positions=5, max_weight=0.25, risk_off=False):
        # candidates: list of dict {symbol, score, risk_grade, confidence, asset_type}
        filtered = []
        for c in candidates:
            rg = str(c.get("risk_grade","C")).upper()
            if rg in {"D","NO_TRADE"}:
                continue
            if float(c.get("confidence",0) or 0) < 55:
                continue
            filtered.append(c)
        filtered = sorted(filtered, key=lambda x: float(x.get("score",0) or 0), reverse=True)[:max_positions]
        raw = {c["symbol"]: float(c.get("score",50)) * (float(c.get("confidence",50))/100) for c in filtered}
        weights = self.normalize(raw)
        if risk_off:
            weights = {k: round(v*0.5,4) for k,v in weights.items()}
        weights = {k: min(v,max_weight) for k,v in weights.items()}
        s = sum(weights.values()) or 1
        weights = {k: round(v/s,4) for k,v in weights.items()}
        return {"positions": filtered, "weights": weights, "cash_policy": "RAISE_CASH" if risk_off else "NORMAL"}

    def exposure_summary(self, positions, weights):
        by_asset = {}
        for p in positions:
            a = p.get("asset_type","UNKNOWN")
            by_asset[a] = by_asset.get(a,0) + weights.get(p["symbol"],0)
        return {"asset_exposure": {k: round(v,4) for k,v in by_asset.items()}, "position_count": len(positions)}
