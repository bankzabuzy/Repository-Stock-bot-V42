
# V1438.2 LINE FORMAT

def format(symbol, data):

    return f"""
🇺🇸 {symbol} | V1438.2 FULL INTEGRATION
Score: {data.get('score')}
Bias: {data.get('bias')}

📊 Status:
{'🟢 BUY' if data.get('score',50)>65 else '🔴 SELL' if data.get('score',50)<40 else '🟡 WAIT'}

Live integrated engine active
"""
