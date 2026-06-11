
from __future__ import annotations
from datetime import datetime, timezone, timedelta

EVENTS = ["FOMC", "CPI", "NFP", "Powell Speech", "Earnings Season"]

def event_prediction():
    now = datetime.now(timezone.utc)
    # Free deterministic approximation: weekly risk windows; replace with real economic calendar API later.
    weekday = now.weekday()
    items = []
    for e in EVENTS:
        if e == "FOMC":
            days = (2 - weekday) % 7
            impact = "HIGH"
            rec = "WAIT_EVENT ถ้าใกล้กว่า 24 ชม."
        elif e == "CPI":
            days = (1 - weekday) % 7
            impact = "HIGH"
            rec = "ลด position ก่อนข่าวเงินเฟ้อ"
        elif e == "NFP":
            days = (4 - weekday) % 7
            impact = "HIGH"
            rec = "ระวัง USD/Yield กระชาก"
        elif e == "Powell Speech":
            days = (3 - weekday) % 7
            impact = "MEDIUM_HIGH"
            rec = "เพิ่ม threshold signal"
        else:
            days = max(1, (0 - weekday) % 7)
            impact = "MEDIUM"
            rec = "ดู guidance และ sector rotation"
        prob = 85 if days <= 1 and impact == "HIGH" else 65 if days <= 2 else 45
        items.append({"event": e, "days_estimate": days, "impact": impact, "probability": prob, "recommendation": rec})
    nearest = sorted(items, key=lambda x: (x["days_estimate"], -x["probability"]))[0]
    decision = "WAIT_EVENT" if nearest["days_estimate"] <= 1 and nearest["impact"] == "HIGH" else "NORMAL_WITH_EVENT_AWARENESS"
    return {"ok": True, "decision": decision, "nearest_event": nearest, "events": items, "note": "ต่อ economic calendar จริงภายหลังได้"}
