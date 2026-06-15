
from fastapi import FastAPI

app = FastAPI()

# health check (Railway will hit this)
@app.get("/")
def health():
    return {
        "status": "OK",
        "version": "V1438.3_DEPLOY_FIXED",
        "message": "DEPLOY SUCCESS ENTRY ACTIVE"
    }

# compatibility for gunicorn
application = app
