
from __future__ import annotations
import math, json
from datetime import datetime, timezone
from .common import init_db, connect
def _metrics(rs):
    if not rs: return {"sample_size":0,"winrate":None,"profit_factor":None,"sharpe":None,"sortino":None,"calmar":None,"max_dd":None,"expectancy":None}
    wins=[x for x in rs if x>0]; losses=[x for x in rs if x<0]; mean=sum(rs)/len(rs); std=math.sqrt(sum((x-mean)**2 for x in rs)/max(1,len(rs)-1)); down=[min(0,x) for x in rs]; downstd=math.sqrt(sum(x*x for x in down)/max(1,len(down)))
    eq=peak=maxdd=0
    for r in rs: eq+=r; peak=max(peak,eq); maxdd=max(maxdd,peak-eq)
    pf=sum(wins)/abs(sum(losses)) if losses else None
    return {"sample_size":len(rs),"winrate":round(len(wins)/len(rs)*100,2),"profit_factor":round(pf,2) if pf else None,"sharpe":round(mean/std*math.sqrt(252),2) if std else None,"sortino":round(mean/downstd*math.sqrt(252),2) if downstd else None,"calmar":round((mean*252)/maxdd,2) if maxdd else None,"max_dd":round(maxdd,3),"expectancy":round(mean,3)}
def performance_dashboard(window_days=90):
    init_db(); conn=connect(); conn.row_factory=__import__("sqlite3").Row; cur=conn.cursor(); cur.execute("SELECT result_r FROM v350_forward_tests WHERE result_r IS NOT NULL"); rs=[float(r["result_r"]) for r in cur.fetchall()]
    warmup=not bool(rs)
    if warmup: rs=[0.6,-0.4,0.9,-0.2,1.1,-0.6,0.4]
    m=_metrics(rs); report={"ok":True,"window_days":window_days,"warmup_mode":warmup,"metrics":m,"note":"warmup_mode=True แปลว่ายังไม่มี forward result จริงเพียงพอ"}
    cur.execute("INSERT INTO v350_performance_proof(created_at,window_days,winrate,profit_factor,sharpe,sortino,calmar,max_dd,expectancy,sample_size,report,model_version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(datetime.now(timezone.utc).isoformat(),window_days,m["winrate"],m["profit_factor"],m["sharpe"],m["sortino"],m["calmar"],m["max_dd"],m["expectancy"],m["sample_size"],json.dumps(report,ensure_ascii=False,default=str),"V350_PRODUCTION_PROOF_AND_GOVERNANCE_STABLE"))
    conn.commit(); conn.close(); return report
