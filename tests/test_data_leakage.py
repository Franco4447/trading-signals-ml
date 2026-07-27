"""
Empirical anti-leakage sanitization test suite.
Validates that features use strict shift(1) without look-ahead bias,
and that parameter calibration (e.g. FracDiff d*) does not leak OOS data.
"""
import numpy as np
import polars as pl

from src.features.technical_indicators import add_advanced_features, find_optimal_d


def test_feature_shift_anti_leakage():
    """
    Empirically verifies that modifying future prices does not affect historical feature values.
    """
    np.random.seed(42)
    n = 200
    df1 = pl.DataFrame({
        "timestamp": pl.datetime_range(pl.datetime(2024, 1, 1), pl.datetime(2024, 1, 10), interval="1h", eager=True)[:n],
        "open": np.random.uniform(40000, 42000, n),
        "high": np.random.uniform(42000, 43000, n),
        "low": np.random.uniform(39000, 40000, n),
        "close": np.random.uniform(40000, 42000, n),
        "volume": np.random.uniform(10, 100, n)
    })

    # Clone and modify ONLY the last price
    df2 = df1.clone()
    close_arr = df2["close"].to_numpy().copy()
    close_arr[-1] += 5000.0  # Big future shock at the last bar
    df2 = df2.with_columns(pl.Series("close", close_arr))

    res1 = add_advanced_features(df1, optimal_d=0.35)
    res2 = add_advanced_features(df2, optimal_d=0.35)

    # Check that feature_zscore_20 and feature_fracdiff up to index N-1 are identical!
    for col in ["feature_zscore_20", "feature_fracdiff", "feature_volatility_20"]:
        arr1 = res1[col].to_numpy()[:-1]
        arr2 = res2[col].to_numpy()[:-1]
        # Ignore initial NaNs
        mask = ~np.isnan(arr1) & ~np.isnan(arr2)
        np.testing.assert_allclose(arr1[mask], arr2[mask], rtol=1e-5, err_msg=f"Data leakage detected in column {col}!")


def test_find_optimal_d_no_oos_leakage():
    """
    Verifies that find_optimal_d with train_ratio does not depend on out-of-sample data.
    """
    np.random.seed(42)
    series = np.random.normal(100, 5, 200).cumsum()

    # Calculate optimal d on series with train_ratio=0.7
    d1 = find_optimal_d(series, train_ratio=0.70)

    # Modify the last 20% of the series (OOS portion)
    series_modified = series.copy()
    series_modified[160:] += 1000.0

    d2 = find_optimal_d(series_modified, train_ratio=0.70)
    assert d1 == d2, "find_optimal_d leaked OOS data into parameter calibration!"
