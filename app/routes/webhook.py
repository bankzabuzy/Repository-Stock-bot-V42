
from fastapi import APIRouter, Request
from app.engine.router import handle_message
from app.services.line_service import reply_message

router = APIRouter()

@router.post("/webhook")
async def webhook(req: Request):
    body = await req.json()

    for e in body.get("events", []):
        if "message" in e:
            msg = e["message"].get("text", "")
            token = e.get("replyToken")

            if token:
                result = handle_message(msg)
                reply_message(token, str(result))

    return {"ok": True}
