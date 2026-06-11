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

def test_api_router_overlay_exists():
    assert "V1300.3 MULTI API ROUTER + REAL HEALTH STATUS" in MAIN
    assert "V1300_3_API_PRIORITY" in MAIN
    assert "v1300_3_api_health_text" in MAIN
    assert "/v1300_3/api-health" in MAIN
    assert "THAI_STOCK" in MAIN
    assert "THAI_GOLD" in MAIN

def test_api_priority_order_exists():
    assert "Polygon.io" in MAIN
    assert "SET official" in MAIN
    assert "GoldTraders" in MAIN
    assert "Yahoo Finance .BK" in MAIN
    assert "XAUUSD × USDTHB" in MAIN

def test_line_commands_exist():
    assert "สถานะapi" in MAIN
    assert "api NVDA" in (ROOT / "VERSION_CURRENT.json").read_text(encoding="utf-8", errors="ignore")
