V1300.1_VERSION = "V1300.1_TOP5_INSTITUTIONAL_COMPAT"


def build_top5():
    """Compatibility placeholder. The production V1300.1 latest-data engine lives in main.py.
    This module exists so older imports do not crash Railway.
    """
    return [
        {"symbol": "TSM", "score": 91, "confidence": 86, "risk_grade": "A", "regime": "STRONG UPTREND", "reason": ["Liquidity สูง", "Trend สนับสนุน"]},
        {"symbol": "QQQ", "score": 88, "confidence": 83, "risk_grade": "A-", "regime": "UPTREND", "reason": ["Liquidity สูง", "Trend สนับสนุน"]},
        {"symbol": "SCB", "score": 86, "confidence": 81, "risk_grade": "B+", "regime": "STRONG UPTREND", "reason": ["Trend สนับสนุน"]},
        {"symbol": "AAOI", "score": 83, "confidence": 77, "risk_grade": "B", "regime": "UPTREND", "reason": ["มี penalty หุ้นผันผวนสูง"]},
        {"symbol": "TJX", "score": 82, "confidence": 77, "risk_grade": "B+", "regime": "STRONG UPTREND", "reason": ["Trend สนับสนุน"]},
    ]
