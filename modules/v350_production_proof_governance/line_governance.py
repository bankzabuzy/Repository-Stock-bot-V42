
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone, timedelta
from .common import init_db, connect
def _key(title,symbol): return hashlib.sha256(f"{title}:{symbol}".encode()).hexdigest()[:16]
def line_alert_governance(title,symbol="SPY",grade="B",message="",cooldown_min=60):
    init_db(); key=_key(title,symbol); now=datetime.now(timezone.utc); conn=connect(); conn.row_factory=__import__("sqlite3").Row; cur=conn.cursor(); cur.execute("SELECT * FROM v350_line_alerts WHERE alert_key=? ORDER BY id DESC LIMIT 1",(key,)); last=cur.fetchone()
    dup=False
    if last:
        try: dup=now<datetime.fromisoformat(last["cooldown_until"])
        except Exception: dup=False
    status="QUEUED" if grade in {"A","A+"} and not dup else "BLOCKED_GRADE" if grade not in {"A","A+"} else "BLOCKED_COOLDOWN"
    until=(now+timedelta(minutes=cooldown_min)).isoformat()
    cur.execute("INSERT INTO v350_line_alerts(created_at,alert_key,grade,title,message,status,retry_count,cooldown_until,payload,model_version) VALUES(?,?,?,?,?,?,?,?,?,?)",(now.isoformat(),key,grade,title,message,status,0,until,json.dumps({"symbol":symbol,"duplicate_block":dup},ensure_ascii=False),"V350_PRODUCTION_PROOF_AND_GOVERNANCE_STABLE"))
    conn.commit(); conn.close(); return {"ok":True,"should_push":status=="QUEUED","status":status,"grade":grade,"alert_key":key,"cooldown_until":until}
def line_governance_status():
    init_db(); conn=connect(); conn.row_factory=__import__("sqlite3").Row; cur=conn.cursor(); cur.execute("SELECT * FROM v350_line_alerts ORDER BY id DESC LIMIT 20"); rows=[dict(r) for r in cur.fetchall()]; conn.close()
    return {"ok":True,"recent":rows,"policy":"Push only A/A+, duplicate cooldown, retry queue ready"}
