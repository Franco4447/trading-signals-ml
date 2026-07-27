"""
Unit tests for Multi-Timeframe Feature Fusion, Dynamic Dollar Bars,
Strict 1d Macro Trend Filter, Pyramiding, Maker Execution, and Weekend Filter.
"""
import numpy as np
import polars as pl
import pytest

from src.data.cleaning import compute_dynamic_dollar_bar_threshold, resample_to_information_bars
from src.execution.ccxt_executor import ExchangeExecutor
from src.execution.paper_trader import PaperTraderEngine
from src.features.technical_indicators import add_multi_timeframe_features
from src.models.signal_scaler import apply_macro_trend_filter, scale_meta_signal
from src.models.triple_barrier import apply_triple_barrier_labeling


def test_dynamic_dollar_bar_threshold():
    dates = pl.datetime_range(start=pl.datetime(2024, 1, 1), end=pl.datetime(2024, 1, 10), interval="1h", eager=True)
    n = len(dates)
    df = pl.DataFrame({
        "timestamp": dates,
        "open": np.full(n, 50000.0),
        "high": np.full(n, 51000.0),
        "low": np.full(n, 49500.0),
        "close": np.full(n, 50500.0),
        "volume": np.full(n, 100.0)
    })
    
    threshold = compute_dynamic_dollar_bar_threshold(df, target_daily_bars=24)
    assert threshold > 0
    
    resample_df = resample_to_information_bars(df, threshold=threshold)
    assert not resample_df.is_empty()
    assert "close" in resample_df.columns


def test_multi_timeframe_join_asof():
    dates_1h = pl.datetime_range(start=pl.datetime(2024, 1, 1), end=pl.datetime(2024, 1, 5), interval="1h", eager=True)
    dates_1d = pl.datetime_range(start=pl.datetime(2024, 1, 1), end=pl.datetime(2024, 1, 5), interval="1d", eager=True)
    
    n_1h = len(dates_1h)
    n_1d = len(dates_1d)
    
    df_1h = pl.DataFrame({
        "timestamp": dates_1h,
        "open": np.full(n_1h, 40000.0),
        "high": np.full(n_1h, 40500.0),
        "low": np.full(n_1h, 39500.0),
        "close": np.full(n_1h, 40200.0),
        "volume": np.full(n_1h, 50.0)
    })
    
    df_1d = pl.DataFrame({
        "timestamp": dates_1d,
        "open": [39000.0, 40000.0, 41000.0, 42000.0, 43000.0],
        "high": [40000.0, 41000.0, 42000.0, 43000.0, 44000.0],
        "low": [38500.0, 39500.0, 40500.0, 41500.0, 42500.0],
        "close": [39800.0, 40800.0, 41800.0, 42800.0, 43800.0],
        "volume": [1000.0, 1200.0, 1100.0, 1300.0, 1400.0]
    })
    
    df_mtf = add_multi_timeframe_features(df_1h=df_1h, df_1d=df_1d)
    assert "feature_macro_regime_1d" in df_mtf.columns
    assert len(df_mtf) == len(df_1h)


def test_strict_daily_macro_trend_filter():
    raw_signals = np.array([0.7, -0.6, 0.4, -0.8])
    macro_regimes = np.array([-1.0, -1.0, 1.0, 1.0])  # Bearish, Bearish, Bullish, Bullish
    
    filtered = apply_macro_trend_filter(raw_signals, macro_regimes)
    
    # In Bearish regime (-1.0), Long signals (>0) are blocked to 0.0
    assert filtered[0] == 0.0
    assert filtered[1] == -0.6
    
    # In Bullish regime (+1.0), Short signals (<0) are blocked to 0.0
    assert filtered[2] == 0.4
    assert filtered[3] == 0.0


def test_dynamic_triple_barrier_volatility_scaling():
    dates = pl.datetime_range(start=pl.datetime(2024, 1, 1), end=pl.datetime(2024, 1, 2), interval="1h", eager=True)
    n = len(dates)
    prices = 40000.0 + np.linspace(0, 500, n)
    vols = np.full(n, 200.0)
    
    df = pl.DataFrame({
        "timestamp": dates,
        "close": prices,
        "feature_volatility_20": vols,
        "volatility_1d": vols * 0.5  # High short-term vol ratio
    })
    
    df_labeled = apply_triple_barrier_labeling(df, dynamic_volatility_scaling=True)
    assert "label" in df_labeled.columns


def test_pyramiding_and_breakeven_sl():
    engine = PaperTraderEngine(initial_balance=10000.0, max_leverage_cap=10.0)
    
    # 1. Open initial Long
    res1 = engine.process_signal(
        signal_score=0.40,
        current_price=50000.0,
        suggested_leverage=3.0,
        take_profit=52000.0,
        stop_loss=49000.0
    )
    assert res1["status"] == "SUCCESS"
    assert engine.current_position["side"] == 1
    initial_entry = engine.current_position["entry_price"]
    
    # 2. Stronger signal in same direction triggers Pyramiding
    res2 = engine.process_signal(
        signal_score=0.80,
        current_price=51000.0,
        suggested_leverage=4.0,
        take_profit=53000.0,
        stop_loss=50000.0
    )
    assert res2["status"] == "SUCCESS"
    assert res2["executed_trade"]["action"] == "PYRAMID_ADD"
    assert engine.current_position["stop_loss"] == initial_entry  # Breakeven SL


def test_maker_limit_order_execution():
    executor = ExchangeExecutor(is_testnet=True)
    res = executor.execute_signal_order(
        symbol="BTC/USDT",
        signal_score=0.75,
        current_price=50000.0,
        suggested_leverage=5.0,
        take_profit=52000.0,
        stop_loss=48000.0,
        order_type="limit"
    )
    assert res["status"] in ["EXECUTED_MOCK_MAKER", "EXECUTED_LIVE"]
    assert res["maker_fee_pct"] == 0.00020
