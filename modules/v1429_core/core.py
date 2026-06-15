
# V1429 CORE - Hybrid Decision Engine (SAFE INTEGRATION LAYER)

def compute_signal(data):
    price = data.get("price", 0)
    vol = data.get("volume", 1)
    rsi = data.get("rsi", 50)

    # simple adaptive scoring (no hard dependency)
    score = 50

    if rsi < 35:
        score += 20
    if rsi > 65:
        score -= 20

    if vol > 2:
        score += 10

    direction = "NEUTRAL"
    if score >= 65:
        direction = "BULLISH"
    elif score <= 40:
        direction = "BEARISH"

    prob = min(80, max(20, score))

    return {
        "score": score,
        "probability": prob,
        "direction": direction
    }
