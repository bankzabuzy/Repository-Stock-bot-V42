
from __future__ import annotations
from .economic_ai import economic_ai
from .news_sentiment_ai import news_sentiment_ai
from .human_behavior_ai import human_behavior_ai

def market_narrative():
    econ = economic_ai()
    news = news_sentiment_ai()
    human = human_behavior_ai()
    macro = econ.get("macro_regime")
    sentiment = news.get("sentiment")
    greed = human.get("greed_score", 50)
    fear = human.get("fear_score", 50)

    if macro == "LIQUIDITY_SUPPORT" and sentiment == "POSITIVE":
        narrative = "ตลาดกำลังเล่นธีม Liquidity / Soft Landing"
    elif greed > 70:
        narrative = "ตลาดกำลังไล่ราคา / FOMO"
    elif fear > 70:
        narrative = "ตลาดกำลังกลัว Risk Event / Recession"
    elif macro == "INFLATION_COMEBACK":
        narrative = "ตลาดกังวลเงินเฟ้อกลับมา"
    elif macro == "STAGFLATION_RISK":
        narrative = "ตลาดเริ่ม price-in stagflation risk"
    else:
        narrative = "ตลาดกำลังอยู่ในช่วง Mixed Rotation"

    return {"ok": True, "narrative": narrative, "macro": econ, "news": news, "human": human}
