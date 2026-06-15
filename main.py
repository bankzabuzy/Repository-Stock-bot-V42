
from fastapi import FastAPI, Request
import os
import requests
import sqlite3
from openai import OpenAI

app = FastAPI()

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    message_count INTEGER,
    last_message TEXT
)
""")
conn.commit()

def update_user(user_id, text):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    if row:
        cursor.execute("""
        UPDATE users
        SET message_count = message_count + 1,
            last_message = ?
        WHERE user_id = ?
        """, (text, user_id))
    else:
        cursor.execute("""
        INSERT INTO users (user_id, message_count, last_message)
        VALUES (?, 1, ?)
        """, (user_id, text))

    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()

def ask_gpt(user_text, memory):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a sales assistant AI."},
            {"role": "user", "content": f"Memory:{memory}\nUser:{user_text}"}
        ]
    )
    return res.choices[0].message.content

def brain(user_id, text):
    user = get_user(user_id)
    memory = {"count": user[1], "last": user[2]} if user else {"count":0,"last":""}

    if "ราคา" in text:
        return "📦 ราคา 1,690 - 2,490 บาท"

    return ask_gpt(text, memory)

@app.get("/")
def home():
    return {"status":"OK","version":"V1450 ULTRA"}

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    for event in body.get("events", []):
        if event["type"] != "message":
            continue
        if event["message"]["type"] != "text":
            continue

        text = event["message"]["text"]
        token = event["replyToken"]
        user_id = event["source"]["userId"]

        update_user(user_id, text)
        reply = brain(user_id, text)
        send(token, reply)

    return {"status":"ok"}

def send(token, text):
    headers = {
        "Content-Type":"application/json",
        "Authorization":f"Bearer {LINE_TOKEN}"
    }
    data = {
        "replyToken":token,
        "messages":[{"type":"text","text":text}]
    }
    requests.post(LINE_REPLY_URL, headers=headers, json=data)
