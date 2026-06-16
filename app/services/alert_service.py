
alerts = {}

def set_alert(user_id, symbol, target):
    alerts.setdefault(user_id, [])
    alerts[user_id].append({
        "symbol": symbol,
        "target": target
    })


def check_alert(price_data):
    triggered = []

    for user, items in alerts.items():
        for a in items:
            if a["symbol"] == price_data.get("symbol"):
                if price_data.get("price", 0) >= a["target"]:
                    triggered.append((user, a))

    return triggered
