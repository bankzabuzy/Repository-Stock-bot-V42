
V1438.4 STABLE DEPLOY FIX

FIXES:
- Worker crash loop
- Missing app entry
- Gunicorn binding mismatch
- Railway deployment instability

STRUCTURE:
- app.py = HTTP ENTRY POINT
- worker.py = SAFE BACKGROUND LOOP
- engine.py = AI LOGIC ISOLATED
