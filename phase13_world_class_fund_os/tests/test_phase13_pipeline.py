from phase13_world_class_fund_os.ops.phase13_pipeline import Phase13Pipeline

def test_phase13_runs():
    pipe = Phase13Pipeline()
    symbols = ["AAPL", "GLD"]
    snapshot = {
        "AAPL": {"trend_score": 60, "momentum_score": 60, "quality_score": 80, "liquidity_score": 80, "volatility_score": 45},
        "GLD": {"trend_score": 62, "momentum_score": 64, "quality_score": 65, "liquidity_score": 85, "volatility_score": 40},
    }
    result = pipe.run(
        symbols, snapshot,
        {"breadth_score": 55, "volatility_score": 45, "liquidity_score": 80, "trend_score": 60},
        {"retail_euphoria": 50, "panic": 40, "news_sentiment": 60},
        {"cpi_yoy": 3.2},
        {"daily_loss_pct": 0.0, "drawdown_pct": 0.0}
    )
    assert result["version"].startswith("V1300")
    assert result["audit_verified"] is True
