
from fastapi import FastAPI

app = FastAPI(title="V1438.4 STABLE DEPLOY FIX")

@app.get("/")
def health():
    return {
        "status": "OK",
        "version": "V1438.4_STABLE_DEPLOY_FIX",
        "message": "ENTRY POINT WORKING"
    }

# compatibility for gunicorn setups
application = app
