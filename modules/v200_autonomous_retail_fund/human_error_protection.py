
from __future__ import annotations
import os, json
from datetime import datetime, timezone
from .common import init_db, connect, safe_float, V200_VERSION

def human_error_protection(context: dict | None=None) -> dict:
    context = context or {}
    trades_last_hour = int(safe_float(context.get("trades_last_hour"), safe_float(os.getenv("V200_TRADES_LAST_HOUR", "0"), 0)) or 0)
    losing_streak = int(safe_float(context.get("losing_streak"), safe_float(os.getenv("V200_LOSING_STREAK", "0"), 0)) or 0)
    heat = safe_float(context.get("portfolio_heat"), safe_float(os.getenv("V200_PORTFOLIO_HEAT", "0"), 0)) or 0
    added_to_loser = str(context.get("added_to_loser", os.getenv("V200_ADDED_TO_LOSER", "false"))).lower() in {"1","true","yes"}
    moved_sl = str(context.get("moved_sl", os.getenv("V200_MOVED_SL", "false"))).lower() in {"1","true","yes"}

    issues = []
    if trades_last_hour >= 5:
        issues.append(("OVERTRADING", "หยุดเทรด 30 นาทีและรอ signal grade A เท่านั้น"))
    if losing_streak >= 3:
        issues.append(("REVENGE_TRADING_RISK", "ลดขนาดไม้ 50% หรือหยุดระบบชั่วคราว"))
    if heat >= 20:
        issues.append(("PORTFOLIO_HEAT_TOO_HIGH", "ห้ามเปิดไม้ใหม่จนกว่า heat ต่ำกว่า 15%"))
    if added_to_loser:
        issues.append(("AVERAGING_DOWN_WARNING", "ห้ามถัวขาดทุนถ้าไม่ใช่แผนที่กำหนดไว้ก่อนเข้า"))
    if moved_sl:
        issues.append(("STOP_LOSS_DISCIPLINE_BREAK", "ห้ามเลื่อน SL หนีขาดทุน"))

    severity = "CRITICAL" if len(issues) >= 3 else "HIGH" if issues else "LOW"
    decision = "BLOCK_NEW_TRADES" if severity in {"CRITICAL","HIGH"} else "ALLOW"

    init_db()
    for typ, rec in issues:
        try:
            conn = connect(); cur = conn.cursor()
            cur.execute("INSERT INTO v200_human_error_events(created_at,error_type,severity,symbol,message,recommendation,payload) VALUES(?,?,?,?,?,?,?)",
                        (datetime.now(timezone.utc).isoformat(), typ, severity, context.get("symbol"), typ, rec, json.dumps(context, ensure_ascii=False, default=str)))
            conn.commit(); conn.close()
        except Exception:
            pass
    return {"ok": True, "severity": severity, "decision": decision, "issues": [{"type": t, "recommendation": r} for t,r in issues]}
