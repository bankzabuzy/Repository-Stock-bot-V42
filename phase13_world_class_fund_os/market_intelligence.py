
from __future__ import annotations
import math, statistics, time, random
from dataclasses import dataclass, asdict

@dataclass
class MarketSignal:
    symbol: str
    price: float
    signal: str
    score: float
    probability: float
    confidence: float
    risk: str
    regime: str
    behavior_note: str
    allocation_hint: float
    reason: str

DEFAULT_SYMBOLS = ["GLD", "NVDA", "AAPL", "TSLA", "QQQ", "SPY", "AMD", "META"]

def _stable_seed(symbol: str) -> int:
    return sum((i+1)*ord(c) for i,c in enumerate(symbol.upper()))

def synthetic_price(symbol: str) -> float:
    seed=_stable_seed(symbol)
    return round(50 + (seed % 450) + ((seed // 7) % 100)/100, 2)

def score_symbol(symbol: str) -> MarketSignal:
    s=symbol.upper().strip()
    seed=_stable_seed(s)
    trend=(seed % 37) / 36
    momentum=((seed//3) % 41) / 40
    quality=((seed//5) % 43) / 42
    crowd=((seed//7) % 47) / 46
    liquidity=((seed//11) % 53) / 52
    mean_rev=1-abs(momentum-0.5)*2
    behavioral_penalty = max(0.0, crowd-0.78)*18
    score = 100*(0.25*trend+0.20*momentum+0.18*quality+0.15*liquidity+0.12*mean_rev+0.10*(1-crowd)) - behavioral_penalty
    score=max(0,min(100,score))
    prob=max(5,min(95, 35 + score*0.6))
    conf=max(10,min(95, 30 + score*0.55 - behavioral_penalty*0.7))
    if score>=78 and conf>=70:
        signal="STRONG_BUY"
    elif score>=62:
        signal="BUY"
    elif score<=32:
        signal="SELL_OR_AVOID"
    else:
        signal="WATCH"
    risk = "A" if score>=75 and crowd<0.75 else "B" if score>=60 else "C" if score>=45 else "D"
    regime = "RISK_ON" if trend>0.62 and liquidity>0.45 else "RISK_OFF" if liquidity<0.28 or crowd>0.84 else "MIXED"
    behavior_note = "crowd_chasing_risk" if crowd>0.78 else "behavior_confirmed" if momentum>0.55 and trend>0.55 else "wait_for_confirmation"
    allocation_hint = 0.04 if risk=="A" and signal=="STRONG_BUY" else 0.02 if risk in ("A","B") and signal in ("BUY","STRONG_BUY") else 0.01 if signal=="WATCH" else 0.0
    reason = f"trend={trend:.2f}, momentum={momentum:.2f}, quality={quality:.2f}, liquidity={liquidity:.2f}, crowd={crowd:.2f}; {behavior_note}"
    return MarketSignal(s, synthetic_price(s), signal, round(score,2), round(prob,1), round(conf,1), risk, regime, behavior_note, allocation_hint, reason)

def top_signals(symbols=None, limit=10):
    symbols = symbols or DEFAULT_SYMBOLS
    rows=[asdict(score_symbol(x)) for x in symbols]
    rows.sort(key=lambda r: (r["score"], r["confidence"]), reverse=True)
    return rows[:limit]

def market_breadth(symbols=None):
    rows=top_signals(symbols or DEFAULT_SYMBOLS, limit=999)
    avg=sum(r['score'] for r in rows)/len(rows)
    risk_on=sum(1 for r in rows if r['regime']=='RISK_ON')
    risk_off=sum(1 for r in rows if r['regime']=='RISK_OFF')
    regime='RISK_ON' if avg>=62 and risk_on>=risk_off else 'RISK_OFF' if avg<45 or risk_off>risk_on else 'MIXED'
    return {'regime': regime, 'score': round(avg,2), 'risk_on_count': risk_on, 'risk_off_count': risk_off, 'items': len(rows)}
