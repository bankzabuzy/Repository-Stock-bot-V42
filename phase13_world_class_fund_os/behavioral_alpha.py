
from __future__ import annotations

def crowd_psychology_overlay(signal):
    note=signal.get('behavior_note','')
    score=float(signal.get('score',0))
    if note=='crowd_chasing_risk':
        action='WAIT_PULLBACK_OR_CONFIRMATION'
        penalty=12
    elif score>=75:
        action='ALLOW_WITH_RISK_CAP'
        penalty=0
    else:
        action='OBSERVE_ONLY'
        penalty=4
    return {'behavior_action': action, 'behavior_penalty': penalty, 'human_bias_guard': ['FOMO','recency_bias','confirmation_bias']}

def market_reflexivity_check(breadth):
    regime=breadth.get('regime','MIXED')
    if regime=='RISK_OFF':
        return {'reflexivity': 'negative_feedback_loop_possible', 'action': 'reduce_beta_raise_cash_gold'}
    if regime=='RISK_ON':
        return {'reflexivity': 'positive_momentum_supported', 'action': 'allow_leaders_with_trailing_risk'}
    return {'reflexivity': 'unclear', 'action': 'smaller_size_wait'}
