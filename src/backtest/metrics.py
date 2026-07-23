"""
Financial performance metrics calculation for trading strategies.
"""
import numpy as np


def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0, periods_per_year: int = 365) -> float:
    """Calculates Annualized Sharpe Ratio."""
    excess_returns = returns - (risk_free_rate / periods_per_year)
    std_dev = np.std(returns)
    if std_dev == 0:
        return 0.0
    return float(np.mean(excess_returns) / std_dev * np.sqrt(periods_per_year))

def calculate_max_drawdown(cum_returns: np.ndarray) -> float:
    """Calculates Maximum Drawdown from cumulative returns series."""
    peak = np.maximum.accumulate(cum_returns)
    drawdown = (cum_returns - peak) / peak
    return float(np.min(drawdown))
