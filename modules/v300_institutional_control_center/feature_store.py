
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, price, V300_VERSION

def compute_features(symbol: str):
    snap = price(symbol)
    chg = snap.get("change_pct") or 0
    px = snap.get("price") or 0
    features = {
        "price": px,
        "change_pct": chg,
        "momentum_score": max(0, min(100, 50 + chg*8)),
        "risk_score": max(0, min(100, 50 - chg*5)),
    }
    return {"ok": snap.get("ok", False), "symbol": symbol, "features": features, "snapshot": snap}

def update_feature_store(symbols=None):
    init_db()
    symbols = symbols or ["SPY","QQQ","NVDA","TSM","GC=F","BTC-USD"]
    rows = []
    try:
        conn = connect(); cur = conn.cursor()
        for sym in symbols:
            data = compute_features(sym)
            for k,v in data["features"].items():
                key = f"{sym}:{k}"
                cur.execute("INSERT OR REPLACE INTO v300_feature_store(feature_key,symbol,feature_group,feature_value,feature_payload,updated_at,model_version) VALUES(?,?,?,?,?,?,?)",
                            (key, sym, "market_features", float(v or 0), json.dumps(data, ensure_ascii=False, default=str), datetime.now(timezone.utc).isoformat(), V300_VERSION))
                rows.append({"feature_key": key, "value": v})
        conn.commit(); conn.close()
    except Exception as e:
        return {"ok": False, "error": str(e), "rows": rows}
    return {"ok": True, "updated": len(rows), "rows": rows}

def feature_store_status():
    data = update_feature_store()
    return {"ok": data.get("ok"), "version": V300_VERSION, "status": data}
