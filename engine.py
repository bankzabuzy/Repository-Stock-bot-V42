
def compute_score(data):
    rsi = data.get("rsi", 50)
    vol = data.get("volume", 1)

    score = 50

    if rsi < 35:
        score += 12
    elif rsi > 65:
        score -= 12

    if vol > 2:
        score += 8

    return {
        "score": max(0, min(100, score)),
        "bias": "NEUTRAL"
    }
