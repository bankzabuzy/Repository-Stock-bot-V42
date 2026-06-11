from pathlib import Path
import py_compile
import re

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

def test_line_reply_and_push_directly_filter_text():
    assert "def v1300_1_force_filter_before_line_send" in MAIN
    assert "def line_reply(reply_token, text):\n    text = v1300_1_force_filter_before_line_send(text)" in MAIN
    assert "def line_push(user_id, text):\n    text = v1300_1_force_filter_before_line_send(text)" in MAIN

def test_no_old_labels_in_main():
    assert "old-fallback-label" not in MAIN
    assert "old-version-41" not in MAIN
    assert "old-version-42" not in MAIN
    assert "V1300.1_WORLD_CLASS_FINAL" in MAIN
