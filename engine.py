
def compute(data):
    rsi = data.get("rsi", 50)
    vol = data.get("volume", 1)

    score = 50

    if rsi < 35:
        score += 15
    elif rsi > 65:
        score -= 15

    if vol > 2:
        score += 10

    score = max(0, min(100, score))

    return {
        "score": score,
        "bias": "BULLISH" if score > 65 else "BEARISH" if score < 40 else "NEUTRAL"
    }
