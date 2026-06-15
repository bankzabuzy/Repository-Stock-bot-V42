
from __future__ import annotations
import importlib, traceback
from typing import Dict, Any, List
from .state import init_state_db, log_error
from .security import safe_public_config
from .guardrails import alert_gate

V101_VERSION = "V1419_MASTER_CLEAN_FINAL"

MODULES_TO_TEST = [
    "modules.v100_fund_os.fund_os",
    "modules.v100_fund_os.monitoring",
    "modules.v51_institutional_validation_execution",
    "modules.v50_world_class_institutional_stack",
    "modules.v42_gold_institutional_core",
]

def import_self_test() -> Dict[str, Any]:
    results = []
    for m in MODULES_TO_TEST:
        try:
            importlib.import_module(m)
            results.append({"module": m, "ok": True})
        except Exception as e:
            results.append({"module": m, "ok": False, "error": str(e)})
            log_error("import_self_test", f"Import failed: {m}", traceback.format_exc())
    return {"ok": all(r.get("ok") for r in results), "results": results}

def endpoint_self_test() -> Dict[str, Any]:
    tests = {}
    try:
        from modules.v100_fund_os.fund_os import build_fund_os_payload
        tests["v100_fund_os"] = bool(build_fund_os_payload("SPY").get("ok"))
    except Exception as e:
        tests["v100_fund_os"] = False
        log_error("endpoint_self_test", "v100_fund_os failed", str(e))
    try:
        from modules.v101_production_hardening.monitoring import build_v101_payload
        tests["v101_payload"] = True
    except Exception:
        tests["v101_payload"] = False
    return {"ok": all(tests.values()), "tests": tests}

def full_self_test() -> Dict[str, Any]:
    db = init_state_db()
    imports = import_self_test()
    gate = alert_gate()
    cfg = safe_public_config()
    return {
        "ok": bool(db.get("ok")) and bool(imports.get("ok")),
        "version": V101_VERSION,
        "db": db,
        "imports": imports,
        "alert_gate": gate,
        "config": cfg,
    }
