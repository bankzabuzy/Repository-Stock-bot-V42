
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from .common import init_db, connect, safe_float
from .data_providers import provider_fallback_price
def create_forward_signal(symbol="SPY",side="BUY",horizon_days=30):
    init_db(); px=provider_fallback_price(symbol); entry=safe_float(px.get("selected",{}).get("price"),100) or 100; sig="FWD-"+uuid.uuid4().hex[:10].upper()
    conn=connect(); cur=conn.cursor()
    cur.execute("INSERT INTO v350_forward_tests(created_at,signal_id,symbol,side,entry_price,current_price,horizon_days,age_days,mae,mfe,rr,status,result_r,payload,model_version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(datetime.now(timezone.utc).isoformat(),sig,symbol,side,entry,entry,horizon_days,0,0,0,2.0,"OPEN",None,json.dumps(px,ensure_ascii=False,default=str),"V350_PRODUCTION_PROOF_AND_GOVERNANCE_STABLE"))
    conn.commit(); conn.close()
    return {"ok":True,"signal_id":sig,"symbol":symbol,"side":side,"entry_price":entry,"horizon_days":horizon_days}
def update_forward_tests():
    init_db(); conn=connect(); conn.row_factory=__import__("sqlite3").Row; cur=conn.cursor(); cur.execute("SELECT * FROM v350_forward_tests WHERE status='OPEN'"); rows=[dict(r) for r in cur.fetchall()]; out=[]
    for r in rows:
        px=provider_fallback_price(r["symbol"]); current=safe_float(px.get("selected",{}).get("price"),r["entry_price"]) or r["entry_price"]; mult=1 if r["side"]=="BUY" else -1
        result=mult*(current-r["entry_price"])/max(.0001,r["entry_price"])*10; age=(datetime.now(timezone.utc)-datetime.fromisoformat(r["created_at"])).total_seconds()/86400; status="CLOSED" if age>=r["horizon_days"] else "OPEN"
        cur.execute("UPDATE v350_forward_tests SET current_price=?,age_days=?,mae=?,mfe=?,status=?,result_r=?,payload=? WHERE id=?",(current,age,min(r.get("mae") or 0,result),max(r.get("mfe") or 0,result),status,result,json.dumps(px,ensure_ascii=False,default=str),r["id"]))
        out.append({"id":r["id"],"symbol":r["symbol"],"result_r":round(result,3),"status":status})
    conn.commit(); conn.close(); return {"ok":True,"updated":len(out),"items":out}
def forward_test_status():
    update_forward_tests(); conn=connect(); conn.row_factory=__import__("sqlite3").Row; cur=conn.cursor(); cur.execute("SELECT * FROM v350_forward_tests ORDER BY id DESC LIMIT 200"); rows=[dict(r) for r in cur.fetchall()]; conn.close()
    if not rows: return {"ok":True,"seeded":[create_forward_signal("SPY","BUY",30),create_forward_signal("QQQ","BUY",60),create_forward_signal("GC=F","BUY",90)],"items":[]}
    return {"ok":True,"count":len(rows),"items":rows}
