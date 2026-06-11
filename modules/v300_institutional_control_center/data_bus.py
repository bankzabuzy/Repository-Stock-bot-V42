
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, price, V300_VERSION

WATCH = ["SPY","QQQ","NVDA","TSM","GC=F","BTC-USD","DX-Y.NYB","^VIX","^TNX","CL=F"]

def publish_market_snapshot(symbol: str):
    init_db()
    snap = price(symbol)
    freshness = 0 if snap.get("ok") else 9999
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v300_data_bus_events(created_at,topic,symbol,payload,freshness_sec,model_version) VALUES(?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), "market_snapshot", symbol, json.dumps(snap, ensure_ascii=False, default=str), freshness, V300_VERSION))
        conn.commit(); conn.close()
    except Exception:
        pass
    return {"ok": True, "topic": "market_snapshot", "symbol": symbol, "freshness_sec": freshness, "payload": snap}

def data_bus_status():
    items = [publish_market_snapshot(s) for s in WATCH]
    bad = [i for i in items if not i.get("payload",{}).get("ok")]
    return {"ok": len(bad) == 0, "version": V300_VERSION, "events": items, "bad_sources": bad, "decision": "DATA_OK" if not bad else "DATA_DEGRADED"}
