import json, os
from pathlib import Path
from datetime import datetime, timezone

class AlertQueue:
    def __init__(self, path="v1411_alert_queue.jsonl"):
        self.path = Path(os.getenv("V1411_ALERT_QUEUE", path))

    def add(self, payload):
        row = {"queued_at_utc": datetime.now(timezone.utc).isoformat(), **(payload or {})}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def tail(self, n=10):
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8", errors="ignore").splitlines()[-n:]:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
        return rows
