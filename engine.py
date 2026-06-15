
def compute(rsi=50, volume=1):
    score = 50

    if rsi < 35:
        score += 15
    elif rsi > 65:
        score -= 15

    if volume > 2:
        score += 10

    return {
        "score": max(0, min(100, score)),
        "bias": "BULLISH" if score > 65 else "BEARISH" if score < 40 else "NEUTRAL"
    }
