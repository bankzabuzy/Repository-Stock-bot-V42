
# V1430 MARKET BRAIN CORE (SAFE HYBRID LAYER)

def market_brain(symbol, data):
    price = data.get("price", 0)
    vol = data.get("volume", 1)
    rsi = data.get("rsi", 50)
    change = data.get("change_pct", 0)

    # freshness scoring (simulate real-time quality)
    freshness = data.get("freshness", 0.8)

    score = 50

    # momentum
    if change > 1:
        score += 10
    if change < -1:
        score -= 10

    # RSI logic
    if rsi < 35:
        score += 18
    if rsi > 65:
        score -= 18

    # volume spike
    if vol > 2:
        score += 12

    # freshness filter (ANTI STALE)
    score = score * freshness

    if score >= 65:
        bias = "BULLISH"
    elif score <= 40:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    return {
        "symbol": symbol,
        "score": round(score, 2),
        "bias": bias,
        "freshness": freshness
    }
