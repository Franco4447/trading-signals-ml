"""
Unit tests for data cleaning and integrity.
"""
from datetime import datetime

import polars as pl

from src.data.cleaning import clean_ohlcv_data


def test_clean_ohlcv_duplicates_and_zeros():
    df = pl.DataFrame({
        "timestamp": [datetime(2026, 1, 1), datetime(2026, 1, 1), datetime(2026, 1, 2)],
        "open": [100.0, 100.0, 105.0],
        "high": [102.0, 102.0, 107.0],
        "low": [99.0, 99.0, 104.0],
        "close": [101.0, 101.0, 0.0], # Row 2 has close 0.0 (invalid)
        "volume": [1000.0, 1000.0, 500.0]
    })
    
    cleaned = clean_ohlcv_data(df)
    
    # Should deduplicate timestamp and drop close <= 0
    assert len(cleaned) == 1
    assert cleaned["close"][0] == 101.0
