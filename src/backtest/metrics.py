"""
Quantitative Financial Metrics Module for Backtesting.
Includes Sharpe Ratio, Sortino Ratio, Max Drawdown, Calmar Ratio, and Profit Factor.
"""
import numpy as np


def calculate_sharpe_ratio(
    returns: np.ndarray,
    risk_free_rate: float = 0.0,
    annualization_factor: float = 365 * 6
) -> float:
    """
    Calculates Annualized Sharpe Ratio.
    """
    if len(returns) == 0 or np.std(returns) == 0:
        return 0.0
    excess_returns = returns - (risk_free_rate / annualization_factor)
    return float(np.mean(excess_returns) / np.std(returns) * np.sqrt(annualization_factor))


def calculate_sortino_ratio(
    returns: np.ndarray,
    risk_free_rate: float = 0.0,
    annualization_factor: float = 365 * 6
) -> float:
    """
    Calculates Annualized Sortino Ratio (downside risk only).
    """
    if len(returns) == 0:
        return 0.0
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0 or np.std(downside_returns) == 0:
        return 0.0
    excess_mean = np.mean(returns) - (risk_free_rate / annualization_factor)
    downside_std = np.sqrt(np.mean(downside_returns**2))
    return float(excess_mean / downside_std * np.sqrt(annualization_factor))


def calculate_max_drawdown(cum_returns: np.ndarray) -> float:
    """
    Calculates Maximum Peak-to-Trough Drawdown.
    """
    if len(cum_returns) == 0:
        return 0.0
    peak = np.maximum.accumulate(cum_returns)
    drawdown = (peak - cum_returns) / peak
    return float(np.max(drawdown))


def calculate_profit_factor(returns: np.ndarray) -> float:
    """
    Calculates Profit Factor (Gross Profits / Gross Losses).
    """
    gains = returns[returns > 0].sum()
    losses = np.abs(returns[returns < 0].sum())
    if losses == 0:
        return float(gains) if gains > 0 else 0.0
    return float(gains / losses)


def calculate_calmar_ratio(cum_returns: np.ndarray, annualization_factor: float = 365 * 6) -> float:
    """
    Calculates Calmar Ratio (Annualized Return / Max Drawdown).
    """
    if len(cum_returns) == 0:
        return 0.0
    total_return = cum_returns[-1] - 1.0
    mdd = calculate_max_drawdown(cum_returns)
    if mdd == 0:
        return 0.0
    ann_return = (1 + total_return)**(annualization_factor / len(cum_returns)) - 1.0
    return float(ann_return / mdd)
