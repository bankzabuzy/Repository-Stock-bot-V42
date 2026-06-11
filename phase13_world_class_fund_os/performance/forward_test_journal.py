from datetime import datetime, timezone

class ForwardTestJournal:
    def __init__(self):
        self.rows = []
    def add(self, payload):
        row = dict(payload)
        row["ts"] = datetime.now(timezone.utc).isoformat()
        self.rows.append(row)
        return row
    def summary(self):
        closed = [r for r in self.rows if "r_multiple" in r]
        if not closed:
            return {"trades": 0, "win_rate": None, "expectancy_r": None}
        wins = sum(1 for r in closed if r["r_multiple"] > 0)
        exp = sum(r["r_multiple"] for r in closed) / len(closed)
        return {"trades": len(closed), "win_rate": round(wins/len(closed)*100,2), "expectancy_r": round(exp,3)}
