
# V1429 ADAPTER - connects old system to V1429 core safely

from modules.v1429_core.core import compute_signal

def v1429_enrich(symbol, snapshot):
    result = compute_signal(snapshot)

    return {
        "symbol": symbol,
        "v1429_score": result["score"],
        "v1429_prob": result["probability"],
        "v1429_bias": result["direction"]
    }
