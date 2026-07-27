"""
Unit tests for the 5 Key Recommendations:
1. Paper Trading Engine & Latency Tracking
2. Multi-Year Dataset Ingestion
3. Hard Circuit Breakers & Leverage Cap
4. Per-Asset Optuna Bayesian Tuning
"""
import numpy as np
import polars as pl

from src.api.server import HARD_MAX_LEVERAGE_CAP
from src.data.ingestion import fetch_multi_year_dataset
from src.execution.paper_trader import PaperTraderEngine
from src.models.optimize import optimize_asset_parameters


def test_paper_trader_execution():
    trader = PaperTraderEngine(initial_balance=10000.0, max_leverage_cap=5.0)
    
    # Process buy signal
    res = trader.process_signal(
        signal_score=0.80,
        current_price=40000.0,
        suggested_leverage=4.0,
        take_profit=42000.0,
        stop_loss=39000.0
    )
    assert res["status"] == "SUCCESS"
    assert trader.current_position is not None
    assert trader.current_position["side"] == 1
    assert "latency_ms" in res


def test_paper_trader_circuit_breaker():
    trader = PaperTraderEngine(initial_balance=10000.0, daily_loss_limit_pct=0.05)
    trader.balance = 9400.0  # Loss of 6% (> 5% limit)
    
    res = trader.process_signal(
        signal_score=0.90,
        current_price=40000.0,
        suggested_leverage=3.0,
        take_profit=42000.0,
        stop_loss=39000.0
    )
    assert res["status"] == "BLOCKED_CIRCUIT_BREAKER"


def test_multi_year_ingestion():
    df_ohlcv, df_micro = fetch_multi_year_dataset(ticker="BTC-USD", symbol="BTC/USDT", years=1, interval="1h")
    assert not df_micro.is_empty()
    assert "funding_rate" in df_micro.columns
    assert "open_interest" in df_micro.columns


def test_optuna_asset_tuning():
    test_data = pl.DataFrame({
        "timestamp": pl.datetime_range(pl.datetime(2024, 1, 1), pl.datetime(2024, 1, 10), interval="1h", eager=True),
        "open": np.random.uniform(40000, 42000, 217),
        "high": np.random.uniform(42000, 43000, 217),
        "low": np.random.uniform(39000, 40000, 217),
        "close": np.random.uniform(40000, 42000, 217),
        "volume": np.random.uniform(10, 100, 217)
    })

    opt_res = optimize_asset_parameters(test_data, symbol="BTC/USDT", n_trials=2)
    assert "best_params" in opt_res
    assert "best_sortino" in opt_res


def test_hard_leverage_cap():
    assert HARD_MAX_LEVERAGE_CAP == 10.0
