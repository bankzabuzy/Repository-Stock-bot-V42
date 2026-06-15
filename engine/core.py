
def safe_engine(data):
    rsi = data.get("rsi", 50)
    vol = data.get("volume", 1)

    score = 50
    if rsi < 35:
        score += 10
    if rsi > 65:
        score -= 10
    if vol > 2:
        score += 5

    return {
        "score": max(0, min(100, score)),
        "bias": "NEUTRAL"
    }
