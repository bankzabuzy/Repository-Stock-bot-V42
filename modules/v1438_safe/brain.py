
def safe_score(data):
    price = data.get("price", 0)
    rsi = data.get("rsi", 50)

    score = 50
    if rsi < 35:
        score += 10
    if rsi > 65:
        score -= 10

    return {
        "score": max(0, min(100, score)),
        "bias": "NEUTRAL"
    }
