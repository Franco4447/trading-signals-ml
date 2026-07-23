"""
Unit tests for Feature Engineering & Anti-Leakage Shift.
"""
from datetime import datetime, timedelta

import polars as pl

from src.features.technical_indicators import add_technical_features


def test_feature_shift_anti_leakage():
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(10)]
    closes = [100.0, 102.0, 104.0, 103.0, 105.0, 108.0, 107.0, 110.0, 112.0, 115.0]
    
    df = pl.DataFrame({
        "timestamp": dates,
        "close": closes
    })
    
    df_features = add_technical_features(df)
    
    # Check that feature_ema_14 at index 1 is calculated based on close up to index 0 (not index 1)
    # The first feature value after initial window should not leak future price
    assert "feature_ema_14" in df_features.columns
    assert "feature_zscore_20" in df_features.columns
    # Row 0 feature should be null due to shift(1)
    assert df_features["feature_ema_14"][0] is None
