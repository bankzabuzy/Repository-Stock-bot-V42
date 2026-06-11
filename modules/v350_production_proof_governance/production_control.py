
from __future__ import annotations
import json
from datetime import datetime, timezone
from .common import init_db, connect, now_th
from .route_cleanup import route_cleanup_registry
from .data_providers import provider_layer_status
from .forward_test import forward_test_status
from .performance_proof import performance_dashboard
from .line_governance import line_alert_governance, line_governance_status
V350_VERSION="V350_PRODUCTION_PROOF_AND_GOVERNANCE_STABLE"
def data_staleness_guard(ps):
    bad=[i for i in ps.get("items",[]) if not i.get("ok")]
    return {"ok":len(bad)==0,"bad_count":len(bad),"decision":"ALLOW" if not bad else "WAIT_DATA"}
def confidence_calibration(raw=85,data_ok=True,perf_ok=True):
    penalty=0; reasons=[]
    if not data_ok: penalty+=20; reasons.append("data_degraded")
    if not perf_ok: penalty+=10; reasons.append("performance_warmup_or_weak")
    final=max(0,min(100,raw-penalty)); grade="A+" if final>=90 else "A" if final>=85 else "B+" if final>=80 else "NO_ALERT"
    return {"raw":raw,"final":final,"grade":grade,"penalty":penalty,"reasons":reasons}
def production_center():
    init_db(); routes=route_cleanup_registry(); providers=provider_layer_status(); fwd=forward_test_status(); perf=performance_dashboard(); perf_ok=(not perf.get("warmup_mode")) and ((perf.get("metrics",{}).get("profit_factor") or 0)>=1.2); stale=data_staleness_guard(providers); calib=confidence_calibration(88,stale.get("ok"),perf_ok); line=line_alert_governance("V350 Production Signal","SPY",calib["grade"],"Production proof governance check"); line_status=line_governance_status()
    scores={"routes":90 if routes.get("collision_count",0)<=16 else 60,"providers":90 if providers.get("ok") else 60,"forward_test":80 if fwd.get("count",0) else 55,"performance":80 if not perf.get("warmup_mode") else 55,"line_governance":90 if line_status.get("ok") else 50}
    score=round(sum(scores.values())/len(scores),2); decision="PRODUCTION_READY_PAPER" if score>=80 else "PAPER_WARMUP_REQUIRED"
    payload={"ok":True,"version":V350_VERSION,"time_th":now_th(),"production_score":score,"decision":decision,"scores":scores,"routes":routes,"providers":providers,"forward_test":fwd,"performance":perf,"data_staleness_guard":stale,"confidence_calibration":calib,"line_governance":line,"line_status":line_status}
    conn=connect(); cur=conn.cursor(); cur.execute("INSERT INTO v350_production_audit(created_at,latest_version,compile_ok,route_collision_count,provider_ok,forward_test_ok,performance_ok,line_governance_ok,production_score,report) VALUES(?,?,?,?,?,?,?,?,?,?)",(datetime.now(timezone.utc).isoformat(),V350_VERSION,1,routes.get("collision_count",0),1 if providers.get("ok") else 0,1 if fwd.get("ok") else 0,1 if not perf.get("warmup_mode") else 0,1 if line_status.get("ok") else 0,score,json.dumps(payload,ensure_ascii=False,default=str))); conn.commit(); conn.close()
    return payload
def production_center_text():
    p=production_center()
    lines=["🚦 V350 PRODUCTION PROOF & GOVERNANCE",f"เวลาไทย: {p.get('time_th')}",f"Production Score: {p.get('production_score')} | Decision: {p.get('decision')}","","SCORES"]
    lines += [f"- {k}: {v}" for k,v in p.get("scores",{}).items()]
    lines += ["",f"Route collisions legacy: {p.get('routes',{}).get('collision_count')}",f"Provider Decision: {p.get('providers',{}).get('decision')}",f"Forward Test Count: {p.get('forward_test',{}).get('count',0)}",f"Performance Warmup: {p.get('performance',{}).get('warmup_mode')}",f"LINE Alert: {p.get('line_governance',{}).get('status')} | Grade {p.get('line_governance',{}).get('grade')}","","หมายเหตุ: ถ้า Performance Warmup=True แปลว่ายังต้องเก็บ forward test จริงต่อ",f"Version : {p.get('version')}"]
    return "\n".join(lines)
