
# TOP5 DYNAMIC ENGINE V1430

def rank(symbols_data):
    ranked = []

    for s in symbols_data:
        score = s.get("score", 0)
        freshness = s.get("freshness", 0.5)

        final = score * freshness
        ranked.append((s["symbol"], final))

    ranked.sort(key=lambda x: x[1], reverse=True)

    return ranked[:5]
