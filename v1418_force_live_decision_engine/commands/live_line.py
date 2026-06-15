from v1418_force_live_decision_engine.engine.live_decision import VERSION, live_decision
from v1415_global_scanner_engine.scanner.global_scanner import global_scan_message
from v1413_worldclass_line_os.api.priority_router import time_th

def money(v, m="US"):
    try:
        if m in {"TH","GOLD"}:
            return f"฿{float(v):,.2f}"
        return f"${float(v):,.2f}"
    except Exception:
        return "N/A"

def live_symbol_message(symbol):
    d = live_decision(symbol)
    s = d["snapshot"]
    m = d["market"]
    q = d["quote"]
    plan = d["plan"]
    em = d["expected"]
    stale_warn = "⚠️ ข้อมูลไม่สดพอ / ห้ามออกสัญญาณจริง" if d["freshness_score"] < 40 else ("⚠️ ข้อมูลอาจล่าช้า" if d["freshness_score"] < 70 else "✅ ข้อมูลสดพอ")
    if plan.get("no_trade"):
        plan_text = f"แผน 3 ไม้: NO TRADE\nเหตุผล: {plan.get('reason')}\nจุดเสี่ยง: {money(plan.get('sl'), m)}"
    else:
        e = plan["entries"]; tp = plan["tp"]
        plan_text = (
            f"ไม้1 {money(e[0][0],m)} | มั่นใจ {e[0][1]}% | เงิน {e[0][2]}%\n"
            f"ไม้2 {money(e[1][0],m)} | มั่นใจ {e[1][1]}% | เงิน {e[1][2]}%\n"
            f"ไม้3 {money(e[2][0],m)} | มั่นใจ {e[2][1]}% | เงิน {e[2][2]}%\n"
            f"TP {money(tp[0],m)} / {money(tp[1],m)} / {money(tp[2],m)}\n"
            f"SL {money(plan['sl'],m)}"
        )
    if m in {"US","ETF"}:
        opt = f"Options: CALL > {money(s.price+s.atr14,m)} | PUT < {money(s.price-s.atr14,m)} | DTE 7–21 วัน"
    else:
        opt = "Options: ไม่มี / ไม่แนะนำ"
    return f"""🧠 FORCE LIVE DECISION | {s.symbol}
เวลา: {time_th()}
Price: {money(s.price,m)} | Mode {q.get('price_mode')} | Source {q.get('source')}
Updated: {q.get('timestamp')} | Fresh {d['freshness_score']}/100 | {stale_warn}

Decision: {d['gate']} | Score {d['decision_score']}/100
มุมมอง: {s.view} | Prob {s.prob_up}% | Conf {s.confidence}% | Risk {s.risk_grade}

คาดการณ์ 1–3 วัน:
ขึ้นถึง {money(em['high_3d'],m)}
ลงถึง {money(em['low_3d'],m)}

Technical: EMA6 {s.ema6:.2f} | EMA12 {s.ema12:.2f} | EMA50 {s.ema50:.2f} | RSI {s.rsi14:.2f}
Volume: ซื้อ {s.buy_ratio}% / ขาย {s.sell_ratio}% | RVOL {s.rvol}

{plan_text}

{opt}

สรุป: {s.key_reason}
Version : {VERSION}"""

def live_scan_message(kind="GLOBAL"):
    # Production-safe batch scanner:
    # ใช้ global scanner/cached snapshot เพื่อไม่ยิง API ทีละหลายสิบตัวจน LINE timeout
    # รายตัว เช่น "nvda" หรือ "live nvda" ยังใช้ Force Live Decision จริง
    base = global_scan_message(kind)
    return base.replace(
        "GLOBAL SCANNER V1415",
        "V1418 SAFE BATCH SCANNER"
    ).replace(
        "GLOBAL SCANNER V1417_CLEAN_LIVE_FINAL",
        "V1418 SAFE BATCH SCANNER"
    ).replace(
        "Top5 คัดจาก Universe ที่สแกน ไม่ใช่ watchlist สั้น",
        "Batch scan ใช้ cache/fallback เพื่อไม่ค้าง; รายตัวใช้ Force Live + Freshness Gate"
    ).replace(
        "Version : V1415_GLOBAL_SCANNER_ENGINE_FINAL",
        "Version : " + VERSION
    ).replace(
        "Version : V1417_CLEAN_LIVE_FINAL",
        "Version : " + VERSION
    )
