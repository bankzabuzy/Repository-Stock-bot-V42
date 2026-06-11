
from __future__ import annotations
import os, re, json, sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

V140_VERSION = "V140_SYSTEM_VERSION_CONSISTENCY_AUDIT_STABLE"
EXPECTED_LATEST = V140_VERSION

def now_th() -> str:
    return datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H:%M")

def project_root() -> Path:
    return Path(__file__).resolve().parents[2]

def db_path() -> str:
    return os.getenv("DB_PATH", "signals.db")

def init_db() -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(db_path())
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS v140_version_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                latest_version TEXT,
                compile_ok INTEGER,
                stale_reference_count INTEGER,
                route_count INTEGER,
                report TEXT
            )
        """)
        conn.commit()
        conn.close()
        return {"ok": True, "db": db_path()}
    except Exception as e:
        return {"ok": False, "db": db_path(), "error": str(e)}

def collect_version_references() -> Dict[str, Any]:
    root = project_root()
    pattern = re.compile(r"V\d+(?:\.\d+)?[A-Z0-9_\.]*")
    refs: Dict[str, List[str]] = {}
    ignore_dirs = {"__pycache__", ".git", ".pytest_cache"}
    for p in root.rglob("*"):
        if any(part in ignore_dirs for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in {".py", ".md", ".txt"}:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            found = sorted(set(pattern.findall(text)))
            if found:
                refs[str(p.relative_to(root))] = found
    return {"ok": True, "latest": EXPECTED_LATEST, "references": refs}

def stale_reference_report() -> Dict[str, Any]:
    data = collect_version_references()
    refs = data.get("references", {})
    stale = {}
    # Old version strings are allowed in README/history and legacy modules, but not in latest dashboard modules/routes.
    latest_sensitive = [
        "main.py",
        "modules/v140_system_version_audit",
        "modules/v130_live_readiness_autonomous",
        "modules/v120_broker_live_ready",
        "modules/v110_retail_institutional_fund",
        "modules/v100_fund_os",
    ]
    for file, versions in refs.items():
        if any(file.startswith(s) or file == s for s in latest_sensitive):
            old = [v for v in versions if v.startswith("V") and not v.startswith("V140") and not v.startswith("V130") and not v.startswith("V120") and not v.startswith("V110") and not v.startswith("V100")]
            # V100/V110/V120/V130 are expected in backward-compatible stack, but should not be presented as latest.
            if old:
                stale[file] = old
    return {
        "ok": True,
        "latest": EXPECTED_LATEST,
        "stale_sensitive_references": stale,
        "stale_reference_count": sum(len(v) for v in stale.values()),
        "note": "V1300.1-V130 references are kept for backward-compatible modules. Latest system status must show V140.",
    }

def route_registry() -> Dict[str, Any]:
    root = project_root()
    routes = []
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in re.finditer(r'@(?:\w+\.)?route\("([^"]+)"', text):
            routes.append({"file": str(p.relative_to(root)), "route": m.group(1)})
    return {"ok": True, "route_count": len(routes), "routes": sorted(routes, key=lambda x: x["route"])}

def latest_status_payload() -> Dict[str, Any]:
    stale = stale_reference_report()
    routes = route_registry()
    return {
        "ok": True,
        "version": V140_VERSION,
        "latest_version": EXPECTED_LATEST,
        "time_th": now_th(),
        "version_audit": stale,
        "route_registry": {"route_count": routes.get("route_count"), "sample": routes.get("routes", [])[:30]},
        "backward_compatibility": {
            "legacy_versions_kept": ["V1300.1", "V50", "V51", "V100", "V110", "V120", "V130"],
            "reason": "ระบบเดิมยังถูกเก็บไว้เพื่อไม่ให้ endpoint เก่าพัง แต่ V140 เป็น latest control layer",
        },
        "latest_endpoints": [
            "/v140/system-center",
            "/v140/system-center-json",
            "/v140/version-audit",
            "/v140/routes",
            "/fund",
            "/v130/governance-center",
            "/v120/broker-center",
            "/v101/production-center",
        ],
    }

def latest_status_text() -> str:
    p = latest_status_payload()
    audit = p.get("version_audit", {})
    lines = [
        "🧩 V140 SYSTEM VERSION CONSISTENCY AUDIT",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        f"Latest Version: {p.get('latest_version')}",
        f"Audit: {'✅ PASS' if audit.get('stale_reference_count') == 0 else '⚠️ CHECK'}",
        f"Sensitive stale refs: {audit.get('stale_reference_count')}",
        "",
        "หมายเหตุ:",
        "ระบบยังเก็บ V1300.1-V130 ไว้เพื่อ backward compatibility",
        "แต่ Control Layer ล่าสุดและ route ตรวจระบบคือ V140",
        "",
        "Latest Endpoints:",
    ]
    lines += [f"- {x}" for x in p.get("latest_endpoints", [])]
    if audit.get("stale_sensitive_references"):
        lines += ["", "Stale sensitive references:"]
        for file, refs in list(audit["stale_sensitive_references"].items())[:10]:
            lines.append(f"- {file}: {refs}")
    lines += ["", f"Version : {V140_VERSION}"]
    return "\n".join(lines)

def save_audit_record(compile_ok: bool = True) -> Dict[str, Any]:
    init_db()
    payload = latest_status_payload()
    try:
        conn = sqlite3.connect(db_path())
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO v140_version_audit(created_at,latest_version,compile_ok,stale_reference_count,route_count,report) VALUES(?,?,?,?,?,?)",
            (
                datetime.now(timezone.utc).isoformat(),
                V140_VERSION,
                1 if compile_ok else 0,
                payload.get("version_audit", {}).get("stale_reference_count", 0),
                payload.get("route_registry", {}).get("route_count", 0),
                json.dumps(payload, ensure_ascii=False, default=str),
            )
        )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return {"ok": True, "audit_id": rid, "payload": payload}
    except Exception as e:
        return {"ok": False, "error": str(e), "payload": payload}
