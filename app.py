from flask import Flask, request
from engine.line_bot import handle_line

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return {"status": "v1419 PRODUCTION+ running"}

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()
    handle_line(body)
    return "OK"

if __name__ == "__main__":
    import os
port = int(os.environ.get("PORT", 8080))
app.run(host="0.0.0.0", port=port)
