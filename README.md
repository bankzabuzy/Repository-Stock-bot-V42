
V1438.6 FIX DEPLOY SPLIT

CHANGES:
- HARD SEPARATION of WEB and WORKER
- Removed all gunicorn from worker path
- Railway-ready dual service structure

DEPLOY:
WEB SERVICE:
  uvicorn app:app

WORKER SERVICE:
  python worker.py
