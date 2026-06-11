
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any
from .common import init_db, connect, V110_VERSION

DEFAULT_MODELS = [
    ("trend_following", "Trend Following", "strategy", 1.0),
    ("mean_reversion", "Mean Reversion", "strategy", 0.8),
    ("momentum", "Momentum", "strategy", 1.0),
    ("breakout", "Breakout", "strategy", 0.7),
    ("ensemble_ai", "Ensemble AI Vote", "ensemble", 1.2),
    ("macro_regime", "Macro Regime Engine", "macro", 1.0),
]

def ensure_models() -> Dict[str, Any]:
    init_db()
    try:
        conn = connect()
        cur = conn.cursor()
        for mid, name, mtype, weight in DEFAULT_MODELS:
            cur.execute("""
                INSERT OR IGNORE INTO v110_model_registry(model_id,model_name,model_type,version,weight,enabled,last_score,updated_at)
                VALUES(?,?,?,?,?,?,?,?)
            """, (mid, name, mtype, V110_VERSION, weight, 1, None, datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()
        return {"ok": True, "models": len(DEFAULT_MODELS)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def registry() -> Dict[str, Any]:
    ensure_models()
    try:
        conn = connect()
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM v110_model_registry ORDER BY model_type, model_id")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"ok": True, "version": V110_VERSION, "models": rows}
    except Exception as e:
        return {"ok": False, "error": str(e), "models": []}
