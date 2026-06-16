
import requests

def get_price(symbol: str):

    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        r = requests.get(url, timeout=5)
        data = r.json()

        result = data["quoteResponse"]["result"]

        if not result:
            return {"error": "not found"}

        s = result[0]

        return {
            "symbol": symbol,
            "price": s.get("regularMarketPrice"),
            "change": s.get("regularMarketChange"),
            "percent": s.get("regularMarketChangePercent")
        }

    except Exception as e:
        return {"error": "stock api failed"}
