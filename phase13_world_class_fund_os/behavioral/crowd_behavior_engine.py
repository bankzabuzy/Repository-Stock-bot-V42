class CrowdBehaviorEngine:
    """
    Models crowd psychology without guaranteeing profit.
    Helps avoid chasing euphoria, panic selling, and revenge trading.
    """
    def score(self, sentiment):
        retail_euphoria = float(sentiment.get("retail_euphoria", 50))
        panic = float(sentiment.get("panic", sentiment.get("fear_index", 50)))
        news = float(sentiment.get("news_sentiment", 50))
        flow = float(sentiment.get("flow_pressure", 50))
        warnings = []
        if retail_euphoria >= 80:
            warnings.append("crowd_euphoria_chasing_risk")
        if panic >= 80:
            warnings.append("panic_market_risk")
        if news <= 25:
            warnings.append("negative_news_cluster")
        if flow <= 25:
            warnings.append("institutional_flow_weak")
        behavioral_score = 50 + (news-50)*0.25 + (flow-50)*0.25 - max(retail_euphoria-70,0)*0.5 - max(panic-70,0)*0.4
        return {"behavioral_score": round(max(0, min(100, behavioral_score)),2), "warnings": warnings}
