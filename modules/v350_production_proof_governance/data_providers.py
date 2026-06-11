
from __future__ import annotations
import json, time
from datetime import datetime, timezone
from .common import init_db, connect, price_yahoo
class Provider:
    name="BASE"; priority=99
    def get_price(self,symbol): return {"ok":False,"provider":self.name,"symbol":symbol,"error":"stub"}
class YahooProvider(Provider):
    name="Yahoo"; priority=1
    def get_price(self,symbol): return price_yahoo(symbol)
class FinnhubProvider(Provider): name="Finnhub"; priority=2
class FMPProvider(Provider): name="FMP"; priority=3
class AlphaVantageProvider(Provider): name="AlphaVantage"; priority=4
class GoldAPIProvider(Provider):
    name="GoldAPI"; priority=0
    def get_price(self,symbol):
        if symbol.upper() in {"XAUUSD","GC=F","GOLD","THAI_GOLD"}:
            d=price_yahoo("GC=F"); d["provider"]="GoldAPI/YahooGoldFallback"; d["symbol"]=symbol; return d
        return {"ok":False,"provider":self.name,"symbol":symbol,"error":"not_gold"}
def providers_for(symbol):
    base=[YahooProvider(),FinnhubProvider(),FMPProvider(),AlphaVantageProvider()]
    return [GoldAPIProvider()]+base if symbol.upper() in {"XAUUSD","GC=F","GOLD","THAI_GOLD"} else base
def provider_fallback_price(symbol):
    init_db(); attempts=[]; selected=None
    for p in providers_for(symbol):
        t=time.time(); d=p.get_price(symbol); d["latency_ms"]=round((time.time()-t)*1000,2); attempts.append(d)
        conn=connect(); cur=conn.cursor()
        cur.execute("INSERT OR REPLACE INTO v350_provider_health(provider,enabled,priority,health_score,latency_ms,last_status,last_error,updated_at) VALUES(?,?,?,?,?,?,?,?)",(p.name,1,p.priority,100 if d.get("ok") else 40,d["latency_ms"],"OK" if d.get("ok") else "FAIL",d.get("error",""),datetime.now(timezone.utc).isoformat()))
        conn.commit(); conn.close()
        if d.get("ok"): selected=d; break
    selected=selected or attempts[0]
    conn=connect(); cur=conn.cursor()
    cur.execute("INSERT INTO v350_provider_prices(created_at,symbol,provider,price,previous_close,data_age_sec,status,payload) VALUES(?,?,?,?,?,?,?,?)",(datetime.now(timezone.utc).isoformat(),symbol,selected.get("provider"),selected.get("price"),selected.get("previous_close"),0 if selected.get("ok") else 9999,"OK" if selected.get("ok") else "FAIL",json.dumps({"selected":selected,"attempts":attempts},ensure_ascii=False,default=str)))
    conn.commit(); conn.close()
    return {"ok":bool(selected.get("ok")),"symbol":symbol,"selected":selected,"attempts":attempts,"decision":"DATA_OK" if selected.get("ok") else "WAIT_DATA"}
def provider_layer_status():
    symbols=["SPY","QQQ","NVDA","TSM","GC=F","BTC-USD"]
    items=[provider_fallback_price(s) for s in symbols]
    return {"ok":all(i.get("ok") for i in items),"items":items,"decision":"ALLOW_SIGNALS" if all(i.get("ok") for i in items) else "WAIT_BAD_DATA"}
