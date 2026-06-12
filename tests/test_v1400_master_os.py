from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8", errors="ignore")

def test_all_python_compile():
    bad = []
    for py in ROOT.rglob("*.py"):
        try:
            py_compile.compile(str(py), doraise=True)
        except Exception as e:
            bad.append((str(py.relative_to(ROOT)), str(e)))
    assert not bad, bad

def test_v1400_modules_exist():
    assert (ROOT / "v1400_master_os" / "journal_ai" / "journal.py").exists()
    assert (ROOT / "v1400_master_os" / "monte_carlo" / "simulator.py").exists()
    assert (ROOT / "v1400_master_os" / "portfolio_engine" / "portfolio.py").exists()
    assert (ROOT / "v1400_master_os" / "risk_engine" / "risk.py").exists()
    assert (ROOT / "v1400_master_os" / "control_center" / "dashboard.py").exists()

def test_v1400_overlay_exists():
    assert "V1400 MASTER OS HEDGEFUND READY OVERLAY" in MAIN
    assert "/v1400/status" in MAIN
    assert "v1400_status_text" in MAIN

def test_version_current():
    txt = (ROOT / "VERSION_CURRENT.json").read_text(encoding="utf-8")
    assert "V1400_MASTER_OS_HEDGEFUND_READY" in txt
