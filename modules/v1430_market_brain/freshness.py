
# DATA FRESHNESS ENGINE

import time

def compute_freshness(last_update_ts):
    now = time.time()
    diff = now - last_update_ts

    # decay model
    if diff < 5:
        return 1.0
    elif diff < 30:
        return 0.9
    elif diff < 120:
        return 0.75
    else:
        return 0.5
