from dataclasses import dataclass

@dataclass
class MarketContext:
    regime: str
    risk_score: float
    liquidity_score: float
    volatility_score: float
    breadth_score: float
    notes: list

class MarketContextEngine:
    def evaluate(self, data):
        breadth = float(data.get("breadth_score", 50))
        vol = float(data.get("volatility_score", 50))
        liquidity = float(data.get("liquidity_score", 70))
        trend = float(data.get("trend_score", 50))
        risk_score = max(0, min(100, trend*0.30 + breadth*0.25 + liquidity*0.25 + (100-vol)*0.20))
        notes = []
        if breadth < 35:
            notes.append("weak_market_breadth")
        if vol > 75:
            notes.append("high_volatility")
        if liquidity < 60:
            notes.append("liquidity_warning")
        regime = "RISK_ON" if risk_score >= 65 else ("RISK_OFF" if risk_score <= 40 else "NEUTRAL")
        return MarketContext(regime, round(risk_score,2), liquidity, vol, breadth, notes)
