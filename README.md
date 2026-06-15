
V1438.5 FINAL STABLE RUNTIME

FIXES:
- Worker restart loop root cause analysis
- Separation of web vs worker runtime
- Railway deployment stabilization

ARCHITECTURE:
- app.py -> WEB API ONLY
- worker.py -> BACKGROUND PROCESS (run separately)
- engine.py -> AI logic isolated
