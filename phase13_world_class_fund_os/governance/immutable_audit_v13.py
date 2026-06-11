import json, hashlib
from datetime import datetime, timezone

class ImmutableAuditV13:
    def __init__(self):
        self.chain = []
    def log(self, event, payload):
        prev = self.chain[-1]["hash"] if self.chain else "GENESIS"
        item = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, "payload": payload, "prev_hash": prev}
        raw = json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)
        item["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        self.chain.append(item)
        return item
    def verify(self):
        prev = "GENESIS"
        for item in self.chain:
            if item["prev_hash"] != prev:
                return False
            clone = dict(item); h = clone.pop("hash")
            raw = json.dumps(clone, ensure_ascii=False, sort_keys=True, default=str)
            if hashlib.sha256(raw.encode()).hexdigest() != h:
                return False
            prev = h
        return True
