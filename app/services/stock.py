
import random

def get_price(symbol):
    return {
        "symbol": symbol,
        "price": round(random.uniform(100, 1000), 2),
        "change": round(random.uniform(-5, 5), 2)
    }
