"""
Advanced Feature Engineering Module using Polars.
Includes Fractional Differentiation (FracDiff d*), Crypto Microstructure Indicators,
Multi-Timeframe trends, and strict Zero Look-Ahead Bias via .shift(1).
"""
import numpy as np
import polars as pl
from statsmodels.tsa.stattools import adfuller

from src.utils.logger import setup_logger

logger = setup_logger("feature_engineering")


def get_fracdiff_weights(d: float, threshold: float = 1e-4, max_lags: int = 100) -> np.ndarray:
    """
    Generates Fractional Differentiation weights (López de Prado).
    """
    weights = [1.0]
    k = 1
    while k < max_lags:
        w_k = -weights[-1] / k * (d - k + 1)
        if abs(w_k) < threshold:
            break
        weights.append(w_k)
        k += 1
    return np.array(weights[::-1])


def fractional_differentiation(series: np.ndarray, d: float, threshold: float = 1e-4) -> np.ndarray:
    """
    Applies Fractional Differentiation to a 1D numpy array.
    """
    weights = get_fracdiff_weights(d, threshold)
    n = len(series)
    k = len(weights)
    fracdiff_series = np.full(n, np.nan)

    if n < k:
        return fracdiff_series

    for i in range(k - 1, n):
        window = series[i - k + 1: i + 1]
        fracdiff_series[i] = np.dot(weights, window)

    return fracdiff_series


def find_optimal_d(series: np.ndarray, p_value_threshold: float = 0.05, train_ratio: float | None = None) -> float:
    """
    Finds minimum exponent d* in [0.0, 1.0] that passes ADF stationarity test (p-value < 0.05).
    If train_ratio is provided, calibrates strictly on the initial training window to avoid look-ahead bias.
    """
    clean_series = series[~np.isnan(series)]
    if train_ratio is not None and 0.0 < train_ratio < 1.0:
        split_idx = max(int(len(clean_series) * train_ratio), 30)
        clean_series = clean_series[:split_idx]

    if len(clean_series) < 30:
        return 0.35  # Default robust fallback for short series

    for d in np.linspace(0.0, 1.0, 21):
        diff_series = fractional_differentiation(clean_series, d)
        valid = diff_series[~np.isnan(diff_series)]
        if len(valid) < 20:
            continue
        try:
            adf_res = adfuller(valid, maxlag=1)
            p_val = adf_res[1]
            if p_val < p_value_threshold:
                logger.info(f"Optimal FracDiff d* selected: {d:.2f} (ADF p-value: {p_val:.4f})")
                return float(d)
        except (ValueError, np.linalg.LinAlgError) as e:
            logger.warning(f"ADF test convergence failed for d={d:.2f}: {e}")
            continue

    return 0.35


def add_advanced_features(
    df: pl.DataFrame,
    microstructure_df: pl.DataFrame = None,
    optimal_d: float = None,
    train_ratio: float | None = 0.7
) -> pl.DataFrame:
    """
    Computes comprehensive quantitative features using Polars vectorized expressions.
    All features enforce .shift(1) to guarantee zero look-ahead bias.
    """
    df_sorted = df.sort("timestamp")
    close_arr = df_sorted["close"].to_numpy()

    if optimal_d is None:
        optimal_d = find_optimal_d(close_arr, train_ratio=train_ratio)

    fracdiff_arr = fractional_differentiation(close_arr, d=optimal_d)

    # Attach FracDiff and base indicators
    features_df = df_sorted.with_columns([
        pl.Series("raw_fracdiff", fracdiff_arr).shift(1).alias("feature_fracdiff"),
        
        # Log Returns (shifted)
        (pl.col("close") / pl.col("close").shift(1)).log().shift(1).alias("feature_log_return_1"),
        (pl.col("close") / pl.col("close").shift(4)).log().shift(1).alias("feature_log_return_4"),
        
        # Trend / EMAs (shifted)
        pl.col("close").ewm_mean(span=14).shift(1).alias("feature_ema_14"),
        pl.col("close").ewm_mean(span=50).shift(1).alias("feature_ema_50"),
        pl.col("close").ewm_mean(span=200).shift(1).alias("feature_ema_200"),
        
        # Volatility / ATR proxy (shifted)
        pl.col("close").rolling_std(window_size=20).shift(1).alias("feature_volatility_20"),
        
        # Rolling Z-Score (shifted)
        ((pl.col("close") - pl.col("close").rolling_mean(window_size=20)) /
         (pl.col("close").rolling_std(window_size=20) + 1e-8)).shift(1).alias("feature_zscore_20"),
    ])

    # Microstructure Features Integration if available
    if microstructure_df is not None and not microstructure_df.is_empty():
        features_df = features_df.with_columns(pl.col("timestamp").dt.replace_time_zone(None).cast(pl.Datetime("ms")))
        microstructure_df = microstructure_df.with_columns(pl.col("timestamp").dt.replace_time_zone(None).cast(pl.Datetime("ms")))
        features_df = features_df.join(microstructure_df, on="timestamp", how="left")
        features_df = features_df.with_columns([
            # Funding Rate Z-score (shifted)
            ((pl.col("funding_rate") - pl.col("funding_rate").rolling_mean(window_size=14)) /
             (pl.col("funding_rate").rolling_std(window_size=14) + 1e-8)).shift(1).alias("feature_funding_zscore"),
            
            # Delta Price / Delta Open Interest Ratio (shifted)
            ((pl.col("close") - pl.col("close").shift(1)) /
             ((pl.col("open_interest") - pl.col("open_interest").shift(1)).abs() + 1e-6)).shift(1).alias("feature_price_oi_ratio")
        ])
    else:
        # Fill zero baseline defaults if microstructure data is absent
        features_df = features_df.with_columns([
            pl.lit(0.0).alias("feature_funding_zscore"),
            pl.lit(0.0).alias("feature_price_oi_ratio")
        ])

    # Fill NaNs created by shifting/rolling with forward fill then 0
    features_df = features_df.fill_null(strategy="forward").fill_null(0.0)

    logger.info(f"Advanced feature engineering completed. Calculated {len(features_df.columns)} columns.")
    return features_df


def add_multi_timeframe_features(
    df_1h: pl.DataFrame,
    df_4h: pl.DataFrame | None = None,
    df_1d: pl.DataFrame | None = None
) -> pl.DataFrame:
    """
    Integrates Multi-Timeframe (MTF) indicators (1d Macro Trend, 4h Volatility Regime) onto the 1h baseline.
    Enforces strict .shift(1) and Polars join_asof(strategy='backward') to eliminate look-ahead bias.
    """
    base_df = add_advanced_features(df_1h)

    # 1. Process 1d Macro Trend Regime if provided
    if df_1d is not None and not df_1d.is_empty():
        df_1d_sorted = df_1d.sort("timestamp")
        df_1d_features = df_1d_sorted.with_columns([
            pl.col("close").ewm_mean(span=200).shift(1).alias("ema200_1d"),
            pl.col("close").rolling_std(window_size=20).shift(1).alias("volatility_1d")
        ]).with_columns([
            # Macro Regime: +1.0 for Bullish (Close > EMA200), -1.0 for Bearish (Close < EMA200)
            (pl.when(pl.col("close").shift(1) >= pl.col("ema200_1d"))
             .then(1.0)
             .otherwise(-1.0)).alias("feature_macro_regime_1d")
        ]).select(["timestamp", "ema200_1d", "volatility_1d", "feature_macro_regime_1d"])

        # Join via join_asof backward
        base_df = base_df.sort("timestamp").join_asof(
            df_1d_features.sort("timestamp"),
            on="timestamp",
            strategy="backward"
        )
    else:
        # Fallback macro regime derived from 1h EMA200 if 1d is not supplied
        base_df = base_df.with_columns([
            (pl.when(pl.col("close").shift(1) >= pl.col("feature_ema_200"))
             .then(1.0)
             .otherwise(-1.0)).alias("feature_macro_regime_1d")
        ])

    # 2. Process 4h Intermediate Volatility Regime if provided
    if df_4h is not None and not df_4h.is_empty():
        df_4h_sorted = df_4h.sort("timestamp")
        df_4h_features = df_4h_sorted.with_columns([
            pl.col("close").rolling_std(window_size=20).shift(1).alias("feature_volatility_4h")
        ]).select(["timestamp", "feature_volatility_4h"])

        base_df = base_df.sort("timestamp").join_asof(
            df_4h_features.sort("timestamp"),
            on="timestamp",
            strategy="backward"
        )
    else:
        base_df = base_df.with_columns([
            pl.col("feature_volatility_20").alias("feature_volatility_4h")
        ])

    base_df = base_df.fill_null(strategy="forward").fill_null(0.0)
    logger.info(f"Multi-Timeframe Feature Integration complete. Resulting columns: {len(base_df.columns)}")
    return base_df

