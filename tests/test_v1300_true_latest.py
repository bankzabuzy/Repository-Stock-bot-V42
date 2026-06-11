
def test_version():
    from phase13_world_class_fund_os.version import VERSION
    assert VERSION.startswith('V1300_')

def test_top_signals():
    from phase13_world_class_fund_os.market_intelligence import top_signals
    rows=top_signals(['GLD','NVDA','AAPL'], 3)
    assert len(rows)==3
    assert all('score' in r for r in rows)
