import os
import tempfile

os.environ['DB_PATH'] = tempfile.mktemp(suffix='.db')

def test_v620_v700_integrated_dashboard_runs():
    from modules.v700_phase7_execution_edge.core import dashboard
    data = dashboard('SPY', 'MIXED')
    assert data['ok'] is True
    assert 'phase6_alpha_discovery' in data
    assert data['position_sizing']['ok'] is True
    assert data['risk_gate'] in {'ALLOW_WITH_HUMAN_APPROVAL', 'BLOCK_NEW_ORDER', 'NO_TRADE_ALPHA_WEAK'}

def test_v620_center_runs():
    from modules.v620_phase6_alpha_discovery_engine.engine import center
    data = center('SPY', 'MIXED')
    assert data['ok'] is True
    assert 'alpha_factory' in data
