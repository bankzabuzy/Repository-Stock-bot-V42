
from __future__ import annotations
from datetime import datetime, timezone
from .common import init_db, connect, V200_VERSION

def record_trade_dna(symbol: str, signal_type: str, market_regime: str, human_behavior: str, macro_narrative: str, raw_confidence: float, adjusted_confidence: float, final_confidence: float):
    init_db()
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v200_trade_dna(created_at,symbol,signal_type,market_regime,human_behavior,macro_narrative,raw_confidence,adjusted_confidence,final_confidence,outcome,pnl_r,model_version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), symbol, signal_type, market_regime, human_behavior, macro_narrative, raw_confidence, adjusted_confidence, final_confidence, "OPEN", None, V200_VERSION))
        conn.commit(); rid = cur.lastrowid; conn.close()
        return {"ok": True, "trade_dna_id": rid}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def self_learning_weight_engine():
    init_db()
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("SELECT market_regime, signal_type, outcome, pnl_r FROM v200_trade_dna WHERE outcome IS NOT NULL AND outcome != 'OPEN'")
        rows = cur.fetchall(); conn.close()
    except Exception:
        rows = []
    groups = {}
    for regime, sig, outcome, pnl in rows:
        key = f"{regime}:{sig}"
        groups.setdefault(key, []).append(float(pnl or 0))
    weights = {}
    for k, vals in groups.items():
        avg = sum(vals)/len(vals)
        weights[k] = round(1.2 if avg > 0.5 else 0.8 if avg < -0.2 else 1.0, 2)
    return {"ok": True, "learning_state": "ACTIVE" if len(rows) >= 30 else "WARMUP", "sample": len(rows), "weights": weights}
