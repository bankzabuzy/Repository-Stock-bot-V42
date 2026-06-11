
from __future__ import annotations
from typing import Dict, Any
from .common import init_db, connect

def incident_summary(limit: int=20) -> Dict[str, Any]:
    init_db()
    try:
        conn = connect()
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM v130_incident_log ORDER BY id DESC LIMIT ?", (limit,))
        items = [dict(r) for r in cur.fetchall()]
        conn.close()
        severity_counts = {}
        for i in items:
            severity_counts[i.get("severity")] = severity_counts.get(i.get("severity"), 0) + 1
        return {"ok": True, "items": items, "severity_counts": severity_counts}
    except Exception as e:
        return {"ok": False, "error": str(e), "items": []}
