
# ANTI STALE FILTER

def is_stale(data):
    return data.get("freshness", 0) < 0.6
