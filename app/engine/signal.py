
def generate_signal(stock):
    if stock["change"] > 2:
        return "BUY"
    if stock["change"] < -2:
        return "SELL"
    return "HOLD"
