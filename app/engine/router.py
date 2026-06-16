
from app.services.stock_service import get_price
from app.services.gpt_service import analyze_stock
from app.services.alert_service import set_alert

def handle_message(text):

    text = text.strip()

    if text.upper().startswith("PRICE"):
        symbol = text.split()[-1]
        return get_price(symbol)

    if text.upper().startswith("ANALYZE"):
        symbol = text.split()[-1]
        data = get_price(symbol)
        return analyze_stock(text, data)

    if text.upper().startswith("SET ALERT"):
        parts = text.split()
        if len(parts) >= 4:
            symbol = parts[2]
            price = float(parts[3])
            set_alert("user", symbol, price)
            return f"SET ALERT {symbol} {price}"
        return "FORMAT: SET ALERT AAPL 200"

    return get_price(text)
