import json, os
from datetime import datetime, timezone
from pathlib import Path

class SimpleSignalStore:
    def __init__(self, path="v1410_signals.jsonl"):
        self.path = Path(os.getenv("V1410_SIGNAL_STORE", path))

    def append(self, payload):
        row = dict(payload)
        row["stored_at_utc"] = datetime.now(timezone.utc).isoformat()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def tail(self, n=5):
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8", errors="ignore").splitlines()
        out = []
        for line in lines[-n:]:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
        return out
