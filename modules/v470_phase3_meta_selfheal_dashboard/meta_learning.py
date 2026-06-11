
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, V470_VERSION

BASE_MODELS = [
    ("Technical AI", "TRENDING", 0.56, 120),
    ("Macro AI", "RISK_OFF", 0.61, 90),
    ("Risk AI", "PANIC", 0.68, 70),
    ("Sentiment AI", "RISK_ON", 0.54, 110),
    ("Options Flow AI", "HIGH_VOLATILITY", 0.52, 40),
]

def meta_learning_weights():
    init_db()
    weights = []
    total_edge = 0
    for name, regime, accuracy, sample in BASE_MODELS:
        edge = max(0.01, (accuracy - 0.50) * (sample / 100))
        total_edge += edge
        weights.append({"model_name": name, "regime": regime, "accuracy": accuracy, "sample_size": sample, "edge": edge})
    for w in weights:
        w["weight"] = round(w["edge"] / total_edge, 4) if total_edge else 0.2
    conn = connect(); cur = conn.cursor()
    for w in weights:
        cur.execute("INSERT INTO v470_meta_learning(created_at,model_name,regime,accuracy,weight,sample_size,report,model_version) VALUES(?,?,?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), w["model_name"], w["regime"], w["accuracy"], w["weight"], w["sample_size"], json.dumps(w, ensure_ascii=False), V470_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V470_VERSION, "weights": weights, "decision": "ADAPTIVE_WEIGHTING_ACTIVE"}

def best_model_for_regime(regime="MIXED"):
    data = meta_learning_weights()
    candidates = [w for w in data["weights"] if w["regime"] == regime]
    if not candidates:
        candidates = data["weights"]
    best = max(candidates, key=lambda x: x["weight"])
    return {"ok": True, "regime": regime, "best_model": best}
