
from fastapi import FastAPI
from app.routes.webhook import router
from app.queue.worker import start_worker

app = FastAPI()

app.include_router(router)

@app.on_event("startup")
def startup():
    start_worker()

@app.get("/")
def home():
    return {"status": "V1450 ULTRA+ RUNNING"}
