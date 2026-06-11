from phase13_world_class_fund_os.ops.phase13_pipeline import Phase13Pipeline
from phase13_world_class_fund_os.security.version_guard import VersionGuard

def main():
    guard = VersionGuard().check_main_preserved(".")
    print("VERSION_GUARD:", guard)
    pipe = Phase13Pipeline()
    symbols = ["GLD", "NVDA", "TSM", "QQQ", "AAPL"]
    snapshot = {
        "GLD": {"trend_score": 60, "momentum_score": 62, "quality_score": 65, "liquidity_score": 85, "volatility_score": 42},
        "NVDA": {"trend_score": 78, "momentum_score": 82, "quality_score": 72, "liquidity_score": 80, "volatility_score": 68},
        "TSM": {"trend_score": 74, "momentum_score": 76, "quality_score": 78, "liquidity_score": 78, "volatility_score": 62},
        "QQQ": {"trend_score": 66, "momentum_score": 68, "quality_score": 70, "liquidity_score": 90, "volatility_score": 55},
        "AAPL": {"trend_score": 58, "momentum_score": 55, "quality_score": 82, "liquidity_score": 88, "volatility_score": 48},
    }
    result = pipe.run(
        symbols=symbols,
        snapshot=snapshot,
        market_data={"breadth_score": 48, "volatility_score": 55, "liquidity_score": 78, "trend_score": 66},
        sentiment={"retail_euphoria": 62, "panic": 42, "news_sentiment": 58, "flow_pressure": 60},
        macro_input={"cpi_yoy": 3.4, "real_yield": 1.0, "usd_strength": 58},
        account={"daily_loss_pct": 0.0, "drawdown_pct": 0.01}
    )
    print(result["message"])
    print("AUDIT_VERIFIED:", result["audit_verified"])

if __name__ == "__main__":
    main()
