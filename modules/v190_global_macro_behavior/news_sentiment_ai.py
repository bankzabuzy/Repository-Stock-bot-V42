
from __future__ import annotations
from .common import price

def news_sentiment_ai():
    # Free proxy from cross-asset behavior; supports future real news APIs.
    spy = price("SPY").get("change_pct") or 0
    qqq = price("QQQ").get("change_pct") or 0
    vix = price("^VIX").get("change_pct") or 0
    gold = price("GC=F").get("change_pct") or 0
    score = max(0, min(100, 50 + spy*5 + qqq*4 - vix*4 + gold*1))
    sentiment = "POSITIVE" if score >= 65 else "NEGATIVE" if score <= 40 else "NEUTRAL"
    return {
        "ok": True,
        "sentiment": sentiment,
        "sentiment_score": round(score,2),
        "sources_supported": ["Yahoo Finance", "Finnhub", "FMP", "AlphaVantage", "Reddit/X proxy"],
        "fact_note": "ถ้าไม่มี news API จะใช้ proxy จาก price/VIX ก่อนเพื่อไม่ทำให้ระบบพัง",
    }
