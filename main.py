
from modules.v1438_integration.brain import integrate

def run(v1419=None, v1437=None, market=None):
    return integrate(v1419, v1437, market)

app = None  # kept for Railway compatibility (safe placeholder)
