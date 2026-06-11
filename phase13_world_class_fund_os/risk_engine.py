
from __future__ import annotations

def portfolio_heat(signals, max_heat=0.12):
    heat=sum(float(s.get('allocation_hint',0)) for s in signals)
    return {'heat': round(heat,4), 'max_heat': max_heat, 'status': 'OK' if heat<=max_heat else 'REDUCE'}

def position_size(signal, equity=100000.0):
    risk_grade=signal.get('risk','C')
    pct={'A':0.04,'B':0.02,'C':0.01,'D':0.0}.get(risk_grade,0.0)
    if signal.get('signal') not in ('BUY','STRONG_BUY'):
        pct=0.0
    amount=equity*pct
    price=max(float(signal.get('price',1)), 1)
    return {'risk_grade': risk_grade, 'risk_pct': pct, 'amount': round(amount,2), 'units': round(amount/price,4)}

def safety_status(live_enabled=False, human_approval=True):
    return {
        'live_trading_enabled': bool(live_enabled),
        'human_approval_required': bool(human_approval),
        'execution_mode': 'LIVE_BLOCKED_SAFE' if not live_enabled else ('LIVE_HUMAN_APPROVAL' if human_approval else 'LIVE_UNSAFE'),
        'kill_switch_ready': True,
    }
