
# CONFLICT RESOLVER (V1438)

def resolve_signals(v1419, v1435, v1437):

    scores = [v1419.get("score",50),
              v1435.get("score",50),
              v1437.get("score",50)]

    final_score = sum(scores) / len(scores)

    if final_score > 65:
        return "BUY", final_score
    if final_score < 40:
        return "SELL", final_score
    return "WAIT", final_score
