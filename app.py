
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def health():
    return {
        "status": "OK",
        "version": "V1438.1_FIX_SAFE",
        "message": "Entry point fixed - system boot stable"
    }

application = app
