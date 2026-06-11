
from __future__ import annotations
from typing import Dict, Any
from .common import init_db, now_th, V110_VERSION
from .execution_simulator import execution_stats
from .daily_report import build_daily_report_text
from .model_registry import registry
from .data_quality import check_data_sources
from .strategy_ranking import strategy_ranking
from .regime_engine import market_regime
from .exposure_control import exposure_control
from .shadow_portfolio import shadow_summary

def build_master_payload() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": V110_VERSION,
        "time_th": now_th(),
        "db": init_db(),
        "data_quality": check_data_sources(),
        "market_regime": market_regime(),
        "exposure_control": exposure_control(),
        "strategy_ranking": strategy_ranking(),
        "model_registry": registry(),
        "execution_stats": execution_stats(),
        "shadow_portfolio": shadow_summary(),
        "daily_report": build_daily_report_text(),
        "endpoints": ["/fund", "/fund-json", "/v110/daily-report", "/v110/data-quality", "/v110/model-registry", "/v110/strategy-ranking", "/v110/shadow-portfolios"],
    }

def build_master_text() -> str:
    p = build_master_payload()
    dq = p["data_quality"]
    reg = p["market_regime"]
    exp = p["exposure_control"]
    rank = p["strategy_ranking"].get("items", [])
    models = p["model_registry"].get("models", [])
    execs = p["execution_stats"]
    shadows = p["shadow_portfolio"].get("items", [])
    lines = [
        "🏛 RETAIL INSTITUTIONAL FUND PLATFORM",
        f"เวลาไทย: {p.get('time_th')}",
        "",
        "SYSTEM",
        f"DB: {'✅' if p.get('db',{}).get('ok') else '❌'} | Version: {p.get('version')}",
        f"Data Quality: {dq.get('decision')} | Sources: {dq.get('sources')}",
        "",
        "MARKET REGIME",
        f"{reg.get('regime')} | Score {reg.get('score')} | Changes {reg.get('changes')}",
        "",
        "EXPOSURE CONTROL",
        f"Decision: {exp.get('decision')} | Cash {exp.get('cash_pct')}% | Breaches {exp.get('breaches')}",
        "",
        "STRATEGY RANKING",
    ]
    for i, r in enumerate(rank[:4], 1):
        lines.append(f"{i}. {r.get('strategy')} | Score {r.get('strategy_score')} | {r.get('recommended_state')}")
    lines += [
        "",
        "MODEL REGISTRY",
        f"Models: {len(models)} | Enabled: {sum(1 for m in models if m.get('enabled'))}",
        "",
        "EXECUTION SIMULATOR",
        f"Fill Rate: {execs.get('fill_rate_pct')} | Avg Slip: {execs.get('avg_slippage')} | Delay: {execs.get('avg_delay_ms')}ms",
        "",
        "SHADOW PORTFOLIO",
        f"Portfolios: {len(shadows)}",
        "",
        "Quick: /fund-json | /v110/daily-report | /v110/data-quality",
        f"Version : {p.get('version')}",
    ]
    return "\n".join(lines)
