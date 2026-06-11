
from __future__ import annotations
from typing import Dict, Any, List
try:
    import yfinance as yf  # type: ignore
except Exception:
    yf = None

def prices(symbol: str, period: str = "1y", interval: str = "1d") -> Dict[str, Any]:
    if yf is None:
        return {"ok": False, "symbol": symbol, "prices": [], "reason": "yfinance_not_available"}
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True, threads=False)
        if df is None or df.empty:
            return {"ok": False, "symbol": symbol, "prices": [], "reason": "no_data"}
        closes = [float(x) for x in df["Close"].dropna().values]
        return {"ok": bool(closes), "symbol": symbol.upper(), "prices": closes, "last": closes[-1] if closes else None}
    except Exception as e:
        return {"ok": False, "symbol": symbol, "prices": [], "reason": str(e)}
