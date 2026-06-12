from dataclasses import dataclass, asdict
from v1413_worldclass_line_os.api.priority_router import normalize_symbol, market_of

@dataclass
class AssetSnapshot:
    symbol: str
    name: str
    price: float
    prev_close: float
    premarket: float | None
    regular: float | None
    afterhours: float | None
    score: int
    prob_up: int
    confidence: int
    risk_grade: str
    view: str
    ema6: float
    ema12: float
    ema50: float
    rsi14: float
    atr14: float
    rvol: float
    pe: float | str
    forward_pe: float | str
    dividend_yield: float | str
    dividend_last: float | str
    buy_ratio: int
    sell_ratio: int
    trend_15m: str
    trend_1h: str
    trend_4h: str
    trend_1d: str
    trend_1w: str
    key_reason: str
    news1: str
    news2: str

FALLBACK = {
    "NVDA": AssetSnapshot("NVDA","NVIDIA",208.19,208.19,202.87,200.42,199.20,34,45,49,"C","BEARISH",211.41,213.67,206.96,40.11,8.57,1.01,30.69,15.75,0.50,0.25,46,54,"Bearish","Bearish","Neutral","Bullish","Bullish","แรงขายยังได้เปรียบ ราคาอยู่ใต้ EMA6/12", "Bond yield และดอลลาร์กระทบหุ้นเทค", "รอแรงซื้อกลับมาก่อนเข้า"),
    "QQQ": AssetSnapshot("QQQ","Nasdaq 100 ETF",707.83,707.83,702.36,693.69,None,42,51,55,"B-","NEUTRAL",720.58,722.64,685.40,52.95,14.09,2.18,30.96,"N/A","N/A",0.73,48,52,"Mixed","Mixed","Neutral","Bullish","Bullish","โมเมนตัมยังไม่ชัด รอ breadth ยืนยัน", "ตลาดเทคแกว่งตาม yield", "รอทะลุแนวต้านก่อนเพิ่มไม้"),
    "SCB.BK": AssetSnapshot("SCB.BK","SCB X",137.50,137.50,None,137.50,None,78,60,64,"B+","BULLISH",137.83,137.25,137.07,58.62,1.82,0.60,10.25,10.32,8.20,9.28,58,42,"N/A","N/A","N/A","Mixed","Mixed","ปันผลเด่น valuation ไม่แพง แต่ volume ยังไม่แรง", "หุ้นธนาคารยังเด่นเชิงปันผล", "ทยอยซื้อได้แต่ไม่ all in"),
    "KBANK.BK": AssetSnapshot("KBANK.BK","Kasikornbank",126.00,126.00,None,126.00,None,67,56,58,"B","WATCH",126.5,125.8,122.0,55.2,1.9,0.75,9.8,"N/A",5.0,"N/A",54,46,"N/A","N/A","N/A","Mixed","Mixed","กลุ่มธนาคารแข็งแต่ต้องรอ volume", "Bank sector ยังมีแรงหนุน", "รอจังหวะย่อ"),
    "BBL.BK": AssetSnapshot("BBL.BK","Bangkok Bank",154.00,154.00,None,154.00,None,65,55,57,"B","WATCH",154.2,153.6,150.0,54.1,2.1,0.72,8.9,"N/A",4.8,"N/A",53,47,"N/A","N/A","N/A","Mixed","Mixed","หุ้น value ต้องรอ volume", "Valuation ไม่แพง", "รอทะลุแนวต้าน"),
    "PTT.BK": AssetSnapshot("PTT.BK","PTT",34.00,34.00,None,34.00,None,61,53,55,"B-","WATCH",34.1,34.0,33.5,51.2,0.45,0.85,10.5,"N/A",5.3,"N/A",51,49,"N/A","N/A","N/A","Mixed","Mixed","ขึ้นกับราคาน้ำมันและตลาดรวม", "Energy sector รอ catalyst", "เข้าเล็กเมื่อยืนแนวรับ"),
    "AOT.BK": AssetSnapshot("AOT.BK","Airports of Thailand",61.00,61.00,None,61.00,None,58,52,54,"C+","WATCH",61.4,61.0,60.0,50.8,0.9,0.70,35.0,"N/A",1.0,"N/A",50,50,"N/A","N/A","N/A","Mixed","Mixed","valuation สูง ต้องรอแรงซื้อชัด", "ท่องเที่ยวฟื้นแต่ราคาไม่ถูก", "รอย่อ"),
    "GOLD": AssetSnapshot("GOLD","Thai Gold",63850,63850,None,63850,None,52,48,44,"C","WAIT",4118,4109,4050,56.2,32.4,1.0,"N/A","N/A","N/A","N/A",45,55,"Neutral","Neutral","Bearish","Bearish","Mixed","รอ London/NY และ DXY/Yield ยืนยัน", "ทองไทยใช้ราคาสมาคมเป็นหลัก", "ยังไม่ใช่จุดไล่ซื้อ"),
}

THAI_GOLD = {
    "bar_buy": 63650,
    "bar_sell": 63850,
    "orn_buy": 62383,
    "orn_sell": 64650,
    "spread": 200,
    "xauusd": 4115.60,
    "usdthb": 32.91,
}

def get_snapshot(symbol: str) -> AssetSnapshot:
    sym = normalize_symbol(symbol)
    if sym in FALLBACK:
        return FALLBACK[sym]
    m = market_of(sym)
    if m == "TH":
        snap = FALLBACK["SCB.BK"]
        data = asdict(snap)
        data.update(symbol=sym, name=sym, score=55, prob_up=51, confidence=50, risk_grade="C+", view="WATCH", key_reason="ยังไม่มีข้อมูลเฉพาะตัว ใช้ fallback แบบระวัง")
        return AssetSnapshot(**data)
    snap = FALLBACK["QQQ"]
    data = asdict(snap)
    data.update(symbol=sym, name=sym, score=50, prob_up=50, confidence=50, risk_grade="C", view="NEUTRAL", key_reason="ยังไม่มีข้อมูลเฉพาะตัว ใช้ fallback แบบระวัง")
    return AssetSnapshot(**data)

def expected_move(s: AssetSnapshot):
    atr = s.atr14 or max(s.price * 0.02, 1)
    high_1d = s.price + atr * 0.55
    low_1d = s.price - atr * 0.85
    high_3d = s.price + atr * 1.25
    low_3d = s.price - atr * 1.55
    down_prob = max(5, 100 - s.prob_up - 5)
    sideways = max(0, 100 - s.prob_up - down_prob)
    return {
        "up_prob": s.prob_up,
        "down_prob": down_prob,
        "sideways_prob": sideways,
        "high_1d": high_1d,
        "low_1d": low_1d,
        "high_3d": high_3d,
        "low_3d": low_3d,
        "expected_pct": (atr / s.price * 100) if s.price else 0,
    }

def trade_plan(s: AssetSnapshot):
    if s.prob_up < 50:
        return {
            "no_trade": True,
            "reason": "Probability ต่ำกว่า 50% รอให้ราคาเลือกทางก่อน",
            "entries": [],
            "tp": [],
            "sl": s.price - s.atr14 * 1.5,
        }
    atr = s.atr14 or max(s.price * 0.01, 1)
    return {
        "no_trade": False,
        "entries": [
            (s.price - atr*0.30, s.confidence, 40),
            (s.price - atr*0.70, max(20, s.confidence-8), 30),
            (s.price - atr*1.10, max(10, s.confidence-20), 30),
        ],
        "tp": [s.price + atr*0.45, s.price + atr*0.95, s.price + atr*1.55],
        "sl": s.price - atr*1.50,
    }

def risk_sentence(s: AssetSnapshot):
    if s.risk_grade.startswith("A"):
        return "🟢 เสี่ยงต่ำ/จังหวะดี"
    if s.risk_grade.startswith("B"):
        return "🟡 เสี่ยงกลาง คุมไม้ได้"
    if s.risk_grade.startswith("C"):
        return "🟠 เสี่ยงสูง ต้องรอจังหวะ"
    return "🔴 หลีกเลี่ยง"

def entry_score(s: AssetSnapshot):
    score = 5.0
    if s.prob_up >= 60: score += 1.2
    if s.rsi14 >= 50: score += 0.6
    if s.rvol >= 1: score += 0.5
    if s.price > s.ema50: score += 0.5
    if s.prob_up < 50: score -= 1.0
    return max(1, min(10, round(score, 1)))
