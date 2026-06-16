
from fastapi import APIRouter, Request
from app.queue.queue import push_task
from app.engine.processor import process_message

router = APIRouter()

@router.post("/webhook")
async def webhook(req: Request):
    body = await req.json()

    for e in body.get("events", []):
        if "message" in e:
            msg = e["message"].get("text", "")
            token = e.get("replyToken")

            def task(msg=msg, token=token):
                process_message(msg, token)

            push_task(task)

    return {"ok": True}
