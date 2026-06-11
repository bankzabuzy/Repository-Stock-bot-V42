
from __future__ import annotations
import os, json
from datetime import datetime, timezone
from .common import init_db, connect, price, V240_VERSION
from .investment_committee import investment_committee

def watchlist_rank():
    raw = os.getenv("V240_WATCHLIST", "NVDA,TSM,SPY,QQQ,GC=F,BTC-USD")
    items = []
    for sym in [s.strip().upper() for s in raw.split(",") if s.strip()]:
        snap = price(sym)
        committee = investment_committee(sym)
        score = (snap.get("change_pct") or 0)*5 + committee.get("final_score", 50)
        items.append({"symbol": sym, "price": snap.get("price"), "change_pct": snap.get("change_pct"), "committee_decision": committee.get("final_decision"), "score": round(score,2)})
    items.sort(key=lambda x: x["score"], reverse=True)
    return {"ok": True, "items": items}

def journal_event(event_type: str, symbol: str, decision: str, reason: str, macro_context: str="", regime: str="", payload=None):
    init_db()
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v240_institutional_journal(created_at,event_type,symbol,decision,reason,macro_context,regime,payload,model_version) VALUES(?,?,?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), event_type, symbol, decision, reason, macro_context, regime, json.dumps(payload or {}, ensure_ascii=False, default=str), V240_VERSION))
        conn.commit(); rid = cur.lastrowid; conn.close()
        return {"ok": True, "journal_id": rid}
    except Exception as e:
        return {"ok": False, "error": str(e)}
