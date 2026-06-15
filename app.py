
from fastapi import FastAPI

app = FastAPI(title="V1438.6 FIX DEPLOY SPLIT")

@app.get("/")
def health():
    return {
        "status": "OK",
        "version": "V1438.6_FIX_DEPLOY_SPLIT",
        "service": "WEB"
    }

application = app
