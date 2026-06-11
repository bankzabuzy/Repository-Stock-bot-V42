"""Phase 12 compatibility CLI. V1300 keeps this file compilable."""

def main():
    try:
        from phase12_world_class_investment_os.ops.phase12_pipeline import Phase12Pipeline
        pipe = Phase12Pipeline()
        result = pipe.run(
            symbols=["AAPL", "NVDA", "TSM", "QQQ", "GLD", "PTT.BK"],
            macro_input={"cpi_yoy": 3.4, "policy_rate": 5.25, "usd_strength": 62},
            sentiment_input={"retail_euphoria": 72, "fear_index": 45, "news_sentiment": 58},
            account={"drawdown_pct": 0.01, "daily_loss_pct": 0.0},
            mode="shadow"
        )
        print(result.get("line_message", result))
        print("AUDIT_VERIFIED:", result.get("audit_verified", False))
    except Exception as exc:
        from phase13_world_class_fund_os.version import VERSION
        print(f"{VERSION} compatibility fallback: {exc}")

if __name__ == "__main__":
    main()
