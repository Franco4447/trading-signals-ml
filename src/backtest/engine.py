"""
Vectorized Backtesting Engine with fee and slippage simulation.
"""
import numpy as np
import polars as pl

from src.backtest.metrics import calculate_max_drawdown, calculate_sharpe_ratio
from src.utils.logger import setup_logger

logger = setup_logger("backtest_engine")

def run_simple_backtest(
    df: pl.DataFrame,
    signal_col: str = "signal",
    price_col: str = "close",
    taker_fee: float = 0.00075,
    slippage: float = 0.0002,
    signal_threshold: float = 0.3
) -> dict:
    """
    Executes vectorized backtest from continuous signal [-1.0, 1.0].
    Applies position sizing based on signal magnitude and subtracts trading friction costs.
    """
    prices = df[price_col].to_numpy()
    signals = df[signal_col].to_numpy()
    
    returns = np.diff(prices) / prices[:-1]
    
    # Filter position by threshold
    positions = np.where(np.abs(signals[:-1]) >= signal_threshold, np.sign(signals[:-1]), 0.0)
    
    # Position change triggers fee friction
    position_changes = np.abs(np.diff(np.insert(positions, 0, 0.0)))
    frictions = position_changes * (taker_fee + slippage)
    
    strategy_returns = positions * returns - frictions
    cum_returns = np.cumprod(1 + strategy_returns)
    
    sharpe = calculate_sharpe_ratio(strategy_returns)
    max_dd = calculate_max_drawdown(cum_returns) if len(cum_returns) > 0 else 0.0
    
    logger.info(f"Backtest Completed. Total Return: {((cum_returns[-1]-1)*100):.2f}%, Sharpe: {sharpe:.2f}, Max DD: {(max_dd*100):.2f}%")
    
    return {
        "total_return": float(cum_returns[-1] - 1) if len(cum_returns) > 0 else 0.0,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
        "strategy_returns": strategy_returns,
        "cum_returns": cum_returns
    }
