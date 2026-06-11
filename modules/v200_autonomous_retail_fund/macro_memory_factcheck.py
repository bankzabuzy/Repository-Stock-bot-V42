
from __future__ import annotations
from datetime import datetime, timezone
from .common import init_db, connect, V200_VERSION

DEFAULT_MEMORY = {
    "TRUMP_TARIFF_EFFECT": ("ภาษี/Trade war เพิ่มความผันผวน USD, หุ้นจีน, inflation expectation", "RISK_OFF_USD_UP"),
    "POWELL_HAWKISH_EFFECT": ("Powell hawkish ทำให้ yield ขึ้น หุ้น growth และ gold ถูกกด", "YIELD_UP_RISK_DOWN"),
    "WAR_RISK_EFFECT": ("สงคราม/ภูมิรัฐศาสตร์หนุน safe haven และเพิ่ม oil shock", "GOLD_OIL_UP_RISK_DOWN"),
    "LIQUIDITY_EASING_EFFECT": ("QE/liquidity easing หนุน risk assets", "RISK_ON"),
}

def ensure_macro_memory():
    init_db()
    try:
        conn = connect(); cur = conn.cursor()
        for k,(desc,bias) in DEFAULT_MEMORY.items():
            cur.execute("INSERT OR IGNORE INTO v200_macro_memory(key,description,impact_bias,last_seen,score,updated_at) VALUES(?,?,?,?,?,?)",
                        (k, desc, bias, None, 50, datetime.now(timezone.utc).isoformat()))
        conn.commit(); conn.close()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def macro_memory():
    ensure_macro_memory()
    try:
        conn = connect(); conn.row_factory = __import__("sqlite3").Row
        cur = conn.cursor(); cur.execute("SELECT * FROM v200_macro_memory")
        rows = [dict(r) for r in cur.fetchall()]; conn.close()
        return {"ok": True, "items": rows}
    except Exception as e:
        return {"ok": False, "error": str(e), "items": []}

def multi_ai_factcheck_consensus(viewpoints: list | None=None):
    viewpoints = viewpoints or ["Technical AI: neutral/bullish", "Macro AI: cautious", "Risk AI: reduce size", "Behavior AI: mixed"]
    caution = sum(1 for v in viewpoints if any(w in v.lower() for w in ["cautious","reduce","risk","bear"]))
    bullish = sum(1 for v in viewpoints if any(w in v.lower() for w in ["bull","risk_on","positive"]))
    if max(caution, bullish) / max(1,len(viewpoints)) >= 0.75:
        status = "CONSENSUS"
    elif max(caution, bullish) / max(1,len(viewpoints)) >= 0.5:
        status = "PARTIAL_CONSENSUS"
    else:
        status = "DISAGREEMENT_LOW_CONFIDENCE"
    return {"ok": True, "status": status, "viewpoints": viewpoints, "caution_votes": caution, "bullish_votes": bullish}
