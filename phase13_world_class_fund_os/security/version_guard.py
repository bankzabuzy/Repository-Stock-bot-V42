from pathlib import Path
class VersionGuard:
    def check_main_preserved(self, root="."):
        p = Path(root) / "main.py"
        if not p.exists():
            return {"ok": False, "reason": "main.py missing"}
        text = p.read_text(encoding="utf-8", errors="ignore")
        lines = text.count("\n") + 1
        return {"ok": lines > 10000, "main_lines": lines, "reason": "full main preserved" if lines > 10000 else "main too short"}
