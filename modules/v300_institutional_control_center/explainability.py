
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, V300_VERSION
from .feature_store import compute_features

def explain_decision(symbol: str="SPY", decision: str="WAIT"):
    init_db()
    f = compute_features(symbol)
    feats = f.get("features", {})
    factors = []
    if feats.get("momentum_score",50) >= 65:
        factors.append({"factor": "momentum", "impact": "positive", "reason": "ราคาแข็งกว่าปกติ"})
    elif feats.get("momentum_score",50) <= 40:
        factors.append({"factor": "momentum", "impact": "negative", "reason": "ราคาอ่อนหรือแรงขายมาก"})
    else:
        factors.append({"factor": "momentum", "impact": "neutral", "reason": "โมเมนตัมยังไม่ชัด"})
    if feats.get("risk_score",50) >= 65:
        factors.append({"factor": "risk", "impact": "negative", "reason": "risk score สูง ต้องลดขนาดไม้"})
    explanation = " | ".join([f"{x['factor']}={x['impact']}: {x['reason']}" for x in factors])
    try:
        conn = connect(); cur = conn.cursor()
        cur.execute("INSERT INTO v300_explainability_logs(created_at,symbol,decision,explanation,factor_report,model_version) VALUES(?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), symbol, decision, explanation, json.dumps(factors, ensure_ascii=False, default=str), V300_VERSION))
        conn.commit(); conn.close()
    except Exception:
        pass
    return {"ok": True, "symbol": symbol, "decision": decision, "explanation": explanation, "factors": factors, "features": feats}
