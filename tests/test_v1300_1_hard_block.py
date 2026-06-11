from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
main_text = (ROOT / "main.py").read_text(encoding="utf-8", errors="ignore")

def test_hard_block_patch_exists():
    assert "V1300.1 HARD BLOCK NO FAKE ANALYSIS" in main_text
    assert "v1300_1_hard_block_no_data_text" in main_text

def test_no_old_versions_in_main():
    assert "old-version-41" not in main_text
    assert "old-version-42" not in main_text
    assert "old-fallback-label" not in main_text

def test_main_preserved():
    assert main_text.count("\n") + 1 > 10000
