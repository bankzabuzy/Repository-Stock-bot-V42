
from __future__ import annotations
import os, sqlite3, json
from datetime import datetime, timezone
from typing import Dict, Any
from .state import db_path, init_state_db

V101_VERSION = "V101_PRODUCTION_HARDENING_SECURITY_STABLE"

def db_summary() -> Dict[str, Any]:
    init_state_db()
    path = db_path()
    result = {"ok": True, "db": path, "tables": {}}
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                result["tables"][t] = cur.fetchone()[0]
            except Exception:
                result["tables"][t] = None
        conn.close()
    except Exception as e:
        result.update({"ok": False, "error": str(e)})
    return result

def backup_manifest() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": V101_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "db_summary": db_summary(),
        "note": "สำหรับ Railway ควร backup DB/volume ภายนอกด้วย ไม่ควรพึ่งไฟล์ใน container อย่างเดียว",
    }
