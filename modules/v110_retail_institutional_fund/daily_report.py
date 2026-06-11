
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from .strategy_ranking import strategy_ranking
from .regime_engine import market_regime
from .exposure_control import exposure_control
from .execution_simulator import execution_stats
from .shadow_portfolio import shadow_summary
from .common import init_db, connect, V110_VERSION

def build_daily_report_text() -> str:
    regime = market_regime()
    exposure = exposure_control()
    ranking = strategy_ranking()
    execs = execution_stats()
    shadows = shadow_summary()
    best = ranking.get("items", [{}])[0] if ranking.get("items") else {}
    worst = ranking.get("items", [{}])[-1] if ranking.get("items") else {}
    text = "\n".join([
        "🏛 DAILY FUND REPORT",
        f"เวลาไทย: {datetime.now(timezone(timedelta(hours=7))).strftime('%d/%m/%Y %H:%M')}",
        "",
        f"Market Regime: {regime.get('regime')} | Score {regime.get('score')}",
        f"Exposure Decision: {exposure.get('decision')} | Breaches: {exposure.get('breaches')}",
        "",
        f"Best Strategy: {best.get('strategy')} | Score {best.get('strategy_score')}",
        f"Worst Strategy: {worst.get('strategy')} | Score {worst.get('strategy_score')}",
        "",
        f"Execution Fill Rate: {execs.get('fill_rate_pct')} | Avg Slippage: {execs.get('avg_slippage')}",
        f"Shadow Portfolios: {len(shadows.get('items', []))}",
        "",
        f"Version : {V110_VERSION}",
    ])
    return text

def save_daily_report() -> Dict[str, Any]:
    init_db()
    report_date = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")
    text = build_daily_report_text()
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO v110_daily_reports(report_date,report_text,created_at,model_version)
            VALUES(?,?,?,?)
        """, (report_date, text, datetime.now(timezone.utc).isoformat(), V110_VERSION))
        conn.commit()
        conn.close()
        return {"ok": True, "report_date": report_date, "report_text": text}
    except Exception as e:
        return {"ok": False, "error": str(e), "report_text": text}
