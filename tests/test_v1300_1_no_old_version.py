from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXT = {".py", ".md", ".txt", ".json", ".toml", ".yml", ".yaml"}
BAD_TOKENS = ("V" + "41", "V" + "42", "SAFE" + "_FALLBACK")

def test_no_old_version_labels():
    bad = []
    for p in ROOT.rglob("*"):
        if p.name.startswith("TEST_REPORT_"):
            continue
        if p == Path(__file__):
            continue
        if p.is_file() and p.suffix.lower() in TEXT_EXT:
            t = p.read_text(encoding="utf-8", errors="ignore")
            if any(tok in t for tok in BAD_TOKENS):
                bad.append(str(p.relative_to(ROOT)))
    assert not bad, bad

def test_main_preserved():
    main = ROOT / "main.py"
    assert main.exists()
    assert main.read_text(encoding="utf-8", errors="ignore").count("\n") + 1 > 10000
