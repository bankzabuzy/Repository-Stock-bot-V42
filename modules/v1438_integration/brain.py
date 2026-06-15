
# V1438.2 FULL INTEGRATION CORE

def integrate(v1419=None, v1437=None, market=None):

    v1419 = v1419 or {"score": 50}
    v1437 = v1437 or {"score": 50}
    market = market or {"rsi": 50, "volume": 1}

    base_score = (v1419.get("score",50) + v1437.get("score",50)) / 2

    # market adjustment
    if market.get("rsi",50) < 35:
        base_score += 10
    if market.get("rsi",50) > 65:
        base_score -= 10

    if market.get("volume",1) > 2:
        base_score += 8

    base_score = max(0, min(100, base_score))

    if base_score > 65:
        bias = "BULLISH"
    elif base_score < 40:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    return {
        "score": base_score,
        "bias": bias
    }
