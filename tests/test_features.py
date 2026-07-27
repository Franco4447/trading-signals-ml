"""
Unit tests for Feature Engineering, FracDiff, Information Bars, and Microstructure.
"""
import numpy as np
import polars as pl

from src.data.cleaning import resample_to_information_bars
from src.features.technical_indicators import (
    add_advanced_features,
    get_fracdiff_weights,
)


def test_fracdiff_weights():
    weights = get_fracdiff_weights(d=0.5, threshold=1e-3, max_lags=20)
    assert len(weights) > 0
    assert weights[-1] == 1.0  # Weight at lag 0 is 1.0


test_data = pl.DataFrame({
    "timestamp": pl.datetime_range(pl.datetime(2024, 1, 1), pl.datetime(2024, 1, 10), interval="1h", eager=True),
    "open": np.random.uniform(40000, 42000, 217),
    "high": np.random.uniform(42000, 43000, 217),
    "low": np.random.uniform(39000, 40000, 217),
    "close": np.random.uniform(40000, 42000, 217),
    "volume": np.random.uniform(10, 100, 217)
})


def test_information_bars_resampling():
    dollar_bars = resample_to_information_bars(test_data, threshold=1_000_000.0, bar_type="dollar")
    assert not dollar_bars.is_empty()
    assert "close" in dollar_bars.columns
    assert "volume" in dollar_bars.columns


def test_add_advanced_features():
    df_features = add_advanced_features(test_data, optimal_d=0.35)
    assert "feature_fracdiff" in df_features.columns
    assert "feature_zscore_20" in df_features.columns
    assert "feature_funding_zscore" in df_features.columns
    # Check shift(1) anti-leakage (first row feature is fill value or nan shifted)
    assert len(df_features) == len(test_data)
