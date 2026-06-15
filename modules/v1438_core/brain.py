
# V1438 FULL EVOLUTION MERGE (SAFE CONSOLIDATED FRAMEWORK)

# NOTE:
# This system merges concepts from V1420–V1437 as DESIGN LAYERS,
# not literal historical re-implementation.

def unified_brain(data):
    price = data.get("price", 0)
    vol = data.get("volume", 1)
    rsi = data.get("rsi", 50)
    sentiment = data.get("sentiment", 0)

    score = 50

    # trend layer (V1419 base)
    if rsi < 35:
        score += 15
    if rsi > 65:
        score -= 15

    # smart money proxy layer (V1433 concept)
    if vol > 2:
        score += 10

    # macro + sentiment layer (V1434 concept)
    score += sentiment * 10

    # volatility stabilization (V1432 concept)
    if data.get("volatility", 1) > 2:
        score -= 10

    score = max(0, min(100, score))

    if score > 65:
        bias = "BULLISH"
    elif score < 40:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    return {
        "score": score,
        "bias": bias
    }
