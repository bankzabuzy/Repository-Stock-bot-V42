from datetime import datetime, timezone

class PaperTradeEngine:
    def __init__(self):
        self.open_positions = []
        self.closed_positions = []

    def open(self, symbol, side, price, size, meta=None):
        pos = {"symbol":symbol,"side":side,"entry":price,"size":size,"meta":meta or {}, "ts":datetime.now(timezone.utc).isoformat()}
        self.open_positions.append(pos)
        return pos

    def close(self, symbol, price):
        for i,p in enumerate(self.open_positions):
            if p["symbol"] == symbol:
                p = self.open_positions.pop(i)
                pnl = (price - p["entry"]) * p["size"] * (1 if p["side"].upper()=="BUY" else -1)
                p.update({"exit":price,"pnl":round(pnl,2),"closed_ts":datetime.now(timezone.utc).isoformat()})
                self.closed_positions.append(p)
                return p
        return None

    def status(self):
        today_pnl = sum(p.get("pnl",0) for p in self.closed_positions)
        return {"open":len(self.open_positions),"closed":len(self.closed_positions),"today_pnl":round(today_pnl,2)}
