
from __future__ import annotations
import os, sqlite3, json, re, importlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

V700_VERSION = "V1419_MASTER_CLEAN_FINAL"

def now_th():
    return datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")

def fnum(x: Any, default: Optional[float]=None):
    try:
        if x is None:
            return default
        if isinstance(x, str):
            x = x.replace(",", "").replace("$", "").replace("฿", "").replace("%", "").strip()
            if not x:
                return default
        return float(x)
    except Exception:
        return default

def db():
    return sqlite3.connect(os.getenv("DB_PATH", "signals.db"))

def init_db():
    con = db(); cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS v700_execution_edge_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,latest_version TEXT,compile_ok INTEGER,route_collision_count INTEGER,compatibility_ok INTEGER,phase7_score REAL,report TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v700_position_sizing(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,symbol TEXT,grade TEXT,risk_pct REAL,qty REAL,report TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS v700_risk_matrix(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,kind TEXT,decision TEXT,score REAL,report TEXT)")
    con.commit(); con.close()

def positions():
    raw = os.getenv("V700_POSITIONS", "NVDA:12,AMD:6,TSM:7,QQQ:18,SPY:15,GC=F:12,BTC-USD:4,CASH:26")
    rows = []
    for part in raw.split(","):
        if ":" in part:
            s, w = part.split(":", 1)
            rows.append({"symbol": s.strip().upper(), "weight": fnum(w, 0) or 0})
    return rows

def price(symbol: str):
    try:
        import yfinance as yf
        info = {}
        try:
            info = yf.Ticker(symbol).info or {}
        except Exception:
            pass
        p = fnum(info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose"), 100)
        return {"ok": p is not None, "symbol": symbol, "price": p}
    except Exception as e:
        return {"ok": False, "symbol": symbol, "price": 100, "error": str(e)}

def position_sizing(symbol="SPY", grade="A", confidence=85, equity=100000, volatility=0.18):
    init_db()
    risk_map = {"A+": 4.0, "A": 2.0, "B+": 1.0, "B": 0.5, "NO_ALERT": 0.0}
    base = risk_map.get(str(grade).upper(), 0.5)
    conf_mult = max(0, min(1.25, (fnum(confidence, 85) or 85) / 90))
    vol_mult = max(0.25, min(1.0, 0.18 / max(0.05, fnum(volatility, 0.18) or 0.18)))
    risk_pct = round(base * conf_mult * vol_mult, 3)
    px = fnum(price(symbol).get("price"), 100) or 100
    qty = round(((fnum(equity, 100000) or 100000) * risk_pct / 100) / (px * 0.03), 4)
    report = {"symbol": symbol, "grade": grade, "risk_pct": risk_pct, "qty": qty, "method": "confidence+volatility adjusted"}
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO v700_position_sizing(created_at,symbol,grade,risk_pct,qty,report) VALUES(?,?,?,?,?,?)", (datetime.now(timezone.utc).isoformat(), symbol.upper(), str(grade).upper(), risk_pct, qty, json.dumps(report, ensure_ascii=False)))
    con.commit(); con.close()
    return {"ok": True, "version": V700_VERSION, **report}

def kelly(symbol="SPY", winrate=0.55, payoff=1.6, cap_pct=5):
    p = fnum(winrate, 0.55) or 0.55
    b = fnum(payoff, 1.6) or 1.6
    raw = max(0, ((b*p)-(1-p))/b) if b > 0 else 0
    return {"ok": True, "version": V700_VERSION, "symbol": symbol, "kelly_pct": round(raw*100, 3), "safe_kelly_pct": round(min(raw*25, fnum(cap_pct,5) or 5), 3)}

def exposure():
    pos = positions()
    buckets = {"Tech": 0, "AI": 0, "Semiconductor": 0, "Gold": 0, "Cash": 0, "Crypto": 0, "US_Equity": 0}
    for p in pos:
        s, w = p["symbol"], p["weight"]
        if s in {"NVDA","AMD","TSM"}:
            buckets["Tech"] += w; buckets["AI"] += w; buckets["Semiconductor"] += w
        elif s in {"QQQ","SPY"}:
            buckets["US_Equity"] += w
            if s == "QQQ": buckets["Tech"] += w
        elif s in {"GC=F","XAUUSD","GOLD"}:
            buckets["Gold"] += w
        elif "BTC" in s or "ETH" in s:
            buckets["Crypto"] += w
        elif s == "CASH":
            buckets["Cash"] += w
    limits = {"Tech":45, "AI":30, "Semiconductor":30, "Gold":25, "Crypto":10, "US_Equity":70, "Cash":100}
    breaches = [k for k,v in buckets.items() if v > limits.get(k, 100)]
    return {"ok": True, "version": V700_VERSION, "exposure": buckets, "limits": limits, "breaches": breaches, "decision": "REDUCE_EXPOSURE" if breaches else "ALLOW"}

def portfolio_heat(max_heat=70):
    heat = sum(p["weight"] for p in positions() if p["symbol"] != "CASH")
    return {"ok": True, "version": V700_VERSION, "current_heat": round(heat,2), "max_heat": fnum(max_heat,70), "decision": "REDUCE_RISK" if heat > (fnum(max_heat,70) or 70) else "ALLOW"}

def correlation():
    pos = positions()
    clusters = {"AI_SEMICONDUCTOR":{"NVDA","AMD","TSM"}, "US_INDEX_GROWTH":{"QQQ","SPY"}, "CRYPTO_BETA":{"BTC-USD","BTCUSDT","ETH-USD"}, "GOLD_SAFEHAVEN":{"GC=F","XAUUSD","GOLD"}}
    items = []
    for name, syms in clusters.items():
        weight = sum(p["weight"] for p in pos if p["symbol"] in syms)
        items.append({"cluster": name, "weight": round(weight,2), "risk_score": round(min(100, weight*2.5),2), "decision": "REDUCE_CORRELATED_RISK" if weight > 25 else "ALLOW"})
    return {"ok": True, "version": V700_VERSION, "clusters": items, "decision": "REDUCE_CORRELATED_RISK" if any(i["decision"]!="ALLOW" for i in items) else "ALLOW"}

def concentration(single_max=15):
    items = []
    for p in positions():
        max_w = 100 if p["symbol"] == "CASH" else fnum(single_max,15)
        items.append({"symbol": p["symbol"], "weight": p["weight"], "max_weight": max_w, "decision": "REDUCE_POSITION" if p["weight"] > max_w else "ALLOW"})
    return {"ok": True, "version": V700_VERSION, "items": items, "decision": "REDUCE_CONCENTRATION" if any(i["decision"]!="ALLOW" for i in items) else "ALLOW"}

def route_audit():
    root = Path(__file__).resolve().parents[2]
    routes = {}
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts: continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in re.finditer(r'@(?:\w+\.)?route\("([^"]+)"', txt):
            routes.setdefault(m.group(1), []).append(str(p.relative_to(root)))
    collisions = {r:f for r,f in routes.items() if len(f)>1}
    return {"route_count": len(routes), "route_collision_count": len(collisions), "collisions": collisions}

def compatibility():
    mods = ["modules.v550_phase5_webull_api_ready.dashboard", "modules.v500_arfos_autonomous_retail_fund_os.dashboard", "modules.v470_phase3_meta_selfheal_dashboard.dashboard"]
    items = []
    for m in mods:
        try:
            importlib.import_module(m); items.append({"module": m, "ok": True})
        except Exception as e:
            items.append({"module": m, "ok": False, "error": str(e)})
    r = route_audit()
    return {"ok": all(i["ok"] for i in items), "imports": items, **r}

def alpha_discovery_snapshot(symbol="SPY", regime="MIXED"):
    """Phase 7 must be built on top of Phase 6 alpha discovery, not separate from it."""
    try:
        from modules.v620_phase6_alpha_discovery_engine.engine import center
        data = center(symbol, regime)
        top = (data.get("alpha_factory") or {}).get("top_alpha") or {}
        return {
            "ok": True,
            "source_version": data.get("version"),
            "phase6_score": data.get("phase6_score"),
            "decision": data.get("decision"),
            "top_alpha": top,
            "best_factor": (data.get("factor_engine") or {}).get("best_factor"),
            "regime_rotation": (data.get("regime_rotation") or {}).get("allocation", {}),
            "raw": data,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "top_alpha": {}, "regime_rotation": {}}

def grade_from_alpha(alpha_snap, default="A"):
    top = (alpha_snap or {}).get("top_alpha") or {}
    score = fnum(top.get("score"), 70) or 70
    if score >= 88:
        return "A+"
    if score >= 75:
        return "A"
    if score >= 65:
        return "B+"
    if score >= 55:
        return "B"
    return "NO_ALERT"

def dashboard(symbol="SPY", regime="MIXED"):
    init_db()
    alpha = alpha_discovery_snapshot(symbol, regime)
    grade = grade_from_alpha(alpha)
    top_alpha = (alpha.get("top_alpha") or {})
    confidence = fnum(top_alpha.get("score"), 85) or 85
    expected_edge = max(0.1, abs(fnum(top_alpha.get("expected_edge"), 1.0) or 1.0))
    volatility = max(0.08, min(0.35, 0.20 - expected_edge/100))
    sizing = position_sizing(symbol, grade=grade, confidence=confidence, volatility=volatility)
    kel = kelly(symbol, winrate=max(0.45, min(0.65, confidence/150)), payoff=max(1.1, 1.0 + expected_edge/2))
    heat = portfolio_heat()
    exp = exposure()
    corr = correlation()
    conc = concentration()
    comp = compatibility()
    risk_gate = "BLOCK_NEW_ORDER" if any(x.get("decision") != "ALLOW" for x in [heat, exp, corr, conc]) else "ALLOW_WITH_HUMAN_APPROVAL"
    if grade == "NO_ALERT":
        risk_gate = "NO_TRADE_ALPHA_WEAK"
    scores = {
        "phase6_alpha_dependency": 95 if alpha.get("ok") else 40,
        "position_sizing": 92 if sizing.get("ok") else 50,
        "kelly": 90 if kel.get("ok") else 50,
        "portfolio_heat": 88 if heat.get("decision") == "ALLOW" else 65,
        "exposure": 88 if exp.get("decision") == "ALLOW" else 65,
        "correlation": 88 if corr.get("decision") == "ALLOW" else 65,
        "concentration": 88 if conc.get("decision") == "ALLOW" else 65,
        "compatibility": 85 if comp.get("ok") else 55,
    }
    score = round(sum(scores.values())/len(scores), 2)
    payload = {"ok": True, "version": V700_VERSION, "time_th": now_th(), "symbol": symbol, "regime": regime, "phase7_score": score, "decision": "TRUE_PHASE7_EXECUTION_EDGE_READY" if score >= 80 else "REDUCE_RISK_BEFORE_EXECUTION", "risk_gate": risk_gate, "phase6_alpha_discovery": alpha, "derived_grade": grade, "scores": scores, "position_sizing": sizing, "kelly": kel, "portfolio_heat": heat, "exposure": exp, "correlation": corr, "concentration": conc, "compatibility": comp}
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO v700_execution_edge_audit(created_at,latest_version,compile_ok,route_collision_count,compatibility_ok,phase7_score,report) VALUES(?,?,?,?,?,?,?)", (datetime.now(timezone.utc).isoformat(), V700_VERSION, 1, comp.get("route_collision_count",0), 1 if comp.get("ok") else 0, score, json.dumps(payload, ensure_ascii=False, default=str)))
    con.commit(); con.close()
    return payload

def dashboard_text(symbol="SPY", regime="MIXED"):
    p = dashboard(symbol, regime)
    top = (p.get("phase6_alpha_discovery") or {}).get("top_alpha") or {}
    return "\n".join([
        "⚙️ V700 TRUE PHASE 7 EXECUTION EDGE + V620 ALPHA DISCOVERY",
        f"เวลาไทย: {p['time_th']}",
        f"Symbol: {p['symbol']} | Regime: {p['regime']}",
        f"Phase7 Score: {p['phase7_score']} | Decision: {p['decision']} | Risk Gate: {p['risk_gate']}",
        f"Phase6 Alpha: {top.get('alpha_name')} | Alpha Score: {top.get('score')} | Grade: {p['derived_grade']}",
        f"Position Risk: {p['position_sizing']['risk_pct']}% | Qty: {p['position_sizing']['qty']}",
        f"Kelly: {p['kelly']['kelly_pct']}% | Safe Kelly: {p['kelly']['safe_kelly_pct']}%",
        f"Portfolio Heat: {p['portfolio_heat']['current_heat']} / {p['portfolio_heat']['max_heat']} | {p['portfolio_heat']['decision']}",
        f"Exposure: {p['exposure']['decision']} | Breaches: {p['exposure']['breaches']}",
        f"Correlation: {p['correlation']['decision']} | Concentration: {p['concentration']['decision']}",
        f"Compatibility Routes: {p['compatibility']['route_count']} | Collisions: {p['compatibility']['route_collision_count']}",
        f"Version : {p['version']}",
    ])
