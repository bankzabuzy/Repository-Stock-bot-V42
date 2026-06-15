
# V1438 UNIFIED SCANNER

def scan(symbols, engine):
    results = []

    for s in symbols:
        data = engine(s)

        results.append({
            "symbol": s,
            "score": data["score"],
            "bias": data["bias"]
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)[:5]
