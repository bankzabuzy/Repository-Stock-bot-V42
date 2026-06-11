
from __future__ import annotations
from datetime import datetime, timezone
import time, json
from .common import init_db, connect, V550_VERSION
from .broker_integration import broker_integration_status

def api_health_center():
    init_db()
    broker_status = broker_integration_status()
    items = []
    conn = connect(); cur = conn.cursor()
    for b in broker_status.get("brokers", []):
        start = time.time()
        latency = round((time.time()-start)*1000 + b.get("latency_ms",0), 2)
        if b.get("broker") == "WEBULL" and b.get("configured"):
            status = "READY_SAFE"
            token = "PRESENT"
            reconnect = "NO_ACTION"
        elif b.get("broker") == "PAPER":
            status = "READY"
            token = "N/A"
            reconnect = "NO_ACTION"
        else:
            status = "MISSING_CONFIG"
            token = "MISSING"
            reconnect = "WAIT_FOR_SECRET"
        item = {"broker": b.get("broker"), "status": status, "latency_ms": latency, "token_status": token, "reconnect_action": reconnect}
        items.append(item)
        cur.execute("INSERT INTO v550_api_health(created_at,broker,status,latency_ms,token_status,reconnect_action,report,model_version) VALUES(?,?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), item["broker"], status, latency, token, reconnect, json.dumps(item, ensure_ascii=False), V550_VERSION))
    conn.commit(); conn.close()
    webull = next((i for i in items if i["broker"] == "WEBULL"), {})
    return {"ok": True, "version": V550_VERSION, "webull_status": webull, "items": items}
