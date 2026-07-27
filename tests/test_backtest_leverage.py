"""
Unit tests for Leverage Backtesting Engine and Liquidation Price simulation.
"""
import numpy as np
import polars as pl

from src.backtest.engine import run_leverage_backtest


def test_leverage_backtest_execution():
    n = 100
    prices = np.linspace(40000, 45000, n)
    signals = np.sin(np.linspace(0, 4 * np.pi, n))  # Oscillating signal [-1, +1]

    df = pl.DataFrame({
        "close": prices,
        "high": prices + 100,
        "low": prices - 100,
        "signal": signals
    })

    res = run_leverage_backtest(df, leverage=3.0, taker_fee=0.00075, slippage=0.0002)

    assert "total_return" in res
    assert "sharpe_ratio" in res
    assert "sortino_ratio" in res
    assert "max_drawdown" in res
    assert "liquidations_count" in res
    assert res["final_capital"] > 0


def test_liquidation_trigger():
    # Price crashes by 50% overnight -> should trigger Long liquidation at 5x leverage
    n = 10
    prices = np.array([40000.0, 40000.0, 39000.0, 20000.0, 20000.0, 20000.0, 20000.0, 20000.0, 20000.0, 20000.0])
    signals = np.array([0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9])

    df = pl.DataFrame({
        "close": prices,
        "high": prices + 100,
        "low": prices - 500,
        "signal": signals
    })

    res = run_leverage_backtest(df, leverage=5.0, signal_threshold=0.3)
    assert res["liquidations_count"] >= 1
