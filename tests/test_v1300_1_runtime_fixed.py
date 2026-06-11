from pathlib import Path
import py_compile
import re

ROOT = Path(__file__).resolve().parents[1]

def test_all_python_compile():
    bad = []
    for py in ROOT.rglob("*.py"):
        try:
            py_compile.compile(str(py), doraise=True)
        except Exception as e:
            bad.append((str(py.relative_to(ROOT)), str(e)))
    assert not bad, bad

def test_main_preserved_and_no_old_fallback():
    main = (ROOT / "main.py").read_text(encoding="utf-8", errors="ignore")
    assert main.count("\n") + 1 > 10000
    assert "SAFE_FALLBACK" not in main
    assert "V41" not in main
    assert "V42" not in main
    assert "V1300.1_WORLD_CLASS_FINAL" in main

def test_no_invalid_decimal_assignment_patterns():
    bad = []
    for py in ROOT.rglob("*.py"):
        text = py.read_text(encoding="utf-8", errors="ignore")
        # invalid cases are assignment/import names such as V1300.1_NAME =
        for m in re.finditer(r"^\s*[A-Za-z_][A-Za-z0-9_]*\.\d+_[A-Za-z_][A-Za-z0-9_]*\s*=", text, flags=re.M):
            bad.append((str(py.relative_to(ROOT)), m.group(0)))
        for m in re.finditer(r"import\s+[A-Za-z_][A-Za-z0-9_]*\.\d+_", text):
            bad.append((str(py.relative_to(ROOT)), m.group(0)))
    assert not bad, bad
