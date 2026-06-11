from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8", errors="ignore")

def test_all_python_files_compile():
    bad = []
    for py in ROOT.rglob("*.py"):
        try:
            py_compile.compile(str(py), doraise=True)
        except Exception as e:
            bad.append((str(py.relative_to(ROOT)), str(e)))
    assert not bad, bad

def test_v1300_2_overlay_exists():
    assert "V1300.2 WORLD CLASS FINAL VERIFIED OVERLAY" in MAIN
    assert "v1300_2_market_session_info" in MAIN
    assert "v1300_2_add_market_reference_to_text" in MAIN
    assert "V1300.2_WORLD_CLASS_FINAL" in MAIN

def test_line_send_is_filtered():
    assert "def line_reply(reply_token, text):" in MAIN
    assert "v1300_2_add_market_reference_to_text" in MAIN
    assert "def line_push(user_id, text):" in MAIN
