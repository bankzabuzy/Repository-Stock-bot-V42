
# V1438.2 TOP5 SCANNER

def scan(symbols, engine):
    results = []

    for s in symbols:
        data = engine(s)

        results.append({
            "symbol": s,
            "score": data.get("score",50),
            "bias": data.get("bias","NEUTRAL")
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)[:5]
