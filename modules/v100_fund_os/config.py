
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Dict, Any

V100_VERSION = "V100_FUND_OPERATING_SYSTEM_STABLE"

@dataclass
class FundConfig:
    mode: str = os.getenv("FUND_MODE", "PAPER")  # PAPER / SHADOW / LIVE
    max_portfolio_heat_pct: float = float(os.getenv("FUND_MAX_HEAT_PCT", "40"))
    max_position_pct: float = float(os.getenv("FUND_MAX_POSITION_PCT", "10"))
    max_daily_loss_pct: float = float(os.getenv("FUND_MAX_DAILY_LOSS_PCT", "2"))
    allow_live_trading: bool = os.getenv("ALLOW_LIVE_TRADING", "false").lower() in {"1", "true", "yes"}
    broker_default: str = os.getenv("BROKER_DEFAULT", "PAPER")
    db_path: str = os.getenv("DB_PATH", "signals.db")
    admin_token_set: bool = bool(os.getenv("ADMIN_TOKEN"))
    line_config_set: bool = bool(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))

def get_config() -> FundConfig:
    return FundConfig()

def config_status() -> Dict[str, Any]:
    cfg = get_config()
    return {
        "version": V100_VERSION,
        "mode": cfg.mode,
        "max_portfolio_heat_pct": cfg.max_portfolio_heat_pct,
        "max_position_pct": cfg.max_position_pct,
        "max_daily_loss_pct": cfg.max_daily_loss_pct,
        "allow_live_trading": cfg.allow_live_trading,
        "broker_default": cfg.broker_default,
        "db_path": cfg.db_path,
        "admin_token_set": cfg.admin_token_set,
        "line_config_set": cfg.line_config_set,
        "safety_note": "LIVE orders are disabled unless ALLOW_LIVE_TRADING=true.",
    }
