"""
Backtest package.
"""
from src.backtest.engine import run_leverage_backtest
from src.backtest.metrics import (
    calculate_calmar_ratio,
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
)

# Alias for backwards compatibility
run_simple_backtest = run_leverage_backtest

__all__ = [
    "run_leverage_backtest",
    "run_simple_backtest",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_max_drawdown",
    "calculate_profit_factor",
    "calculate_calmar_ratio"
]
