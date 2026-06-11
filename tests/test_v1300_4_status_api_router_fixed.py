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

def test_status_fix_overlay_exists():
    assert "V1300.4 STATUS + API ROUTER FIX" in MAIN
    assert "v1300_4_unified_status_text" in MAIN
    assert "POLYGON_API_KEY" in MAIN
    assert "GOLD_API_KEY" in MAIN
    assert "FRED_API_KEY" in MAIN
    assert "THAI_MARKET_API_KEY" in MAIN
    assert "/v1300_4/status" in MAIN

def test_old_quicklinks_are_replaced_in_cleaner():
    assert "/v1300_4/status" in MAIN
    assert "v1300_4_clean_output" in MAIN
