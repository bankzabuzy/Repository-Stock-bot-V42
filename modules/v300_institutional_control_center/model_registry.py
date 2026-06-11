
from __future__ import annotations
from datetime import datetime, timezone
from .common import init_db, connect, V300_VERSION

DEFAULT_MODELS = [
    ("v190_macro_ai","Global Macro AI","macro","V190",1,82,15),
    ("v200_fund_manager","Autonomous Retail Fund","fund_os","V200",1,80,12),
    ("v210_committee","Multi-Agent Committee","agent","V210",1,78,18),
    ("v220_broker_network","Broker Execution Network","execution","V220",1,75,10),
    ("v230_portfolio_os","Live Portfolio OS","portfolio","V230",1,79,11),
    ("v240_fund_manager","Autonomous Fund Manager","governance","V240",1,81,13),
]

def seed_registry():
    init_db()
    conn = connect(); cur = conn.cursor()
    for mid,name,mtype,layer,en,health,drift in DEFAULT_MODELS:
        cur.execute("INSERT OR REPLACE INTO v300_model_registry(model_id,model_name,model_type,owner_layer,version,enabled,health_score,drift_score,notes,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (mid,name,mtype,layer,V300_VERSION,en,health,drift,"registered_by_v300",datetime.now(timezone.utc).isoformat()))
    conn.commit(); conn.close()
    return {"ok": True}

def model_registry_status():
    seed_registry()
    conn = connect(); conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor(); cur.execute("SELECT * FROM v300_model_registry")
    rows = [dict(r) for r in cur.fetchall()]; conn.close()
    drift_alerts = [r for r in rows if (r.get("drift_score") or 0) > 25]
    return {"ok": True, "version": V300_VERSION, "models": rows, "drift_alerts": drift_alerts}
