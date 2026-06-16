
import os
import requests

TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

def reply_message(token, text):

    if not TOKEN:
        print("NO LINE TOKEN")
        return

    url = "https://api.line.me/v2/bot/message/reply"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "replyToken": token,
        "messages": [{"type": "text", "text": str(text)}]
    }

    try:
        requests.post(url, headers=headers, json=data, timeout=5)
    except Exception as e:
        print("LINE ERROR", e)
