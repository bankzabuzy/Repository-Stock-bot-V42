
from app.services.stock import get_price
from app.engine.signal import generate_signal

def process_message(msg, token):
    try:
        stock = get_price(msg.strip().upper())
        signal = generate_signal(stock)

        reply = f"""
STOCK: {stock['symbol']}
PRICE: {stock['price']}
CHANGE: {stock['change']}
SIGNAL: {signal}
"""

        print("REPLY:", reply)

    except Exception as e:
        print("error:", e)
