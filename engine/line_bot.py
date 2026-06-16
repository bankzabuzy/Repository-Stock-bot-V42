import requests
import os

LINE_TOKEN = os.getenv("LINE_TOKEN")

def reply(token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }

    data = {
        "replyToken": token,
        "messages": [{"type": "text", "text": text}]
    }

    requests.post(url, headers=headers, json=data)

def handle_line(body):
    try:
        event = body["events"][0]
        msg = event["message"]["text"]
        token = event["replyToken"]

        reply(token, f"[v1419 PRODUCTION+] {msg}")

    except Exception as e:
        print("LINE ERROR:", e)
