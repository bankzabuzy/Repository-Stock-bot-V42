
from __future__ import annotations
import random, json, math
from datetime import datetime, timezone
from .common import init_db, connect, V430_VERSION

SCENARIOS = {
    "MONTE_CARLO": {"mean": 0.03, "vol": 1.0},
    "CPI_SHOCK": {"mean": -0.45, "vol": 1.5},
    "YIELD_SHOCK": {"mean": -0.55, "vol": 1.4},
    "FLASH_CRASH": {"mean": -1.8, "vol": 2.2},
    "BLACK_SWAN": {"mean": -3.0, "vol": 3.5},
}

def _percentile(vals, q):
    vals = sorted(vals)
    if not vals: return None
    idx = max(0, min(len(vals)-1, int(len(vals)*q)))
    return vals[idx]

def run_scenario(symbol="SPY", scenario="MONTE_CARLO", trials=1000):
    init_db()
    random.seed(430 + len(symbol) + len(scenario))
    cfg = SCENARIOS.get(scenario.upper(), SCENARIOS["MONTE_CARLO"])
    outcomes = [random.gauss(cfg["mean"], cfg["vol"]) for _ in range(max(100, min(int(trials), 5000)))]
    expected = sum(outcomes)/len(outcomes)
    var95 = _percentile(outcomes, 0.05)
    tail = [x for x in outcomes if x <= var95]
    cvar95 = sum(tail)/len(tail) if tail else var95
    pass_gate = not (cvar95 is not None and cvar95 < -3.0) and scenario.upper() != "BLACK_SWAN"
    report = {"symbol": symbol, "scenario": scenario.upper(), "expected_loss": round(expected,3), "var_95": round(var95,3), "cvar_95": round(cvar95,3), "pass_gate": pass_gate, "trials": len(outcomes)}
    conn = connect(); cur = conn.cursor()
    cur.execute("INSERT INTO v430_digital_twin(created_at,symbol,scenario,pass_gate,expected_loss,var_95,cvar_95,report,model_version) VALUES(?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), symbol.upper(), scenario.upper(), 1 if pass_gate else 0, expected, var95, cvar95, json.dumps(report, ensure_ascii=False), V430_VERSION))
    conn.commit(); conn.close()
    return {"ok": True, "version": V430_VERSION, **report}

def digital_twin_gate(symbol="SPY"):
    items = [run_scenario(symbol, s, 1000) for s in SCENARIOS]
    failed = [i for i in items if not i.get("pass_gate")]
    decision = "BLOCK_LIVE_EXECUTION" if failed else "ALLOW_PAPER_ONLY"
    return {"ok": True, "version": V430_VERSION, "decision": decision, "failed": failed, "items": items}
