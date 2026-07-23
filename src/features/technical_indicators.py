"""
Feature engineering module using Polars.
Ensures zero look-ahead bias by shifting technical indicators by 1 bar.
"""
import polars as pl


def add_technical_features(df: pl.DataFrame) -> pl.DataFrame:
    """
    Computes technical indicators using Polars vectorized engine.
    Applies shift(1) to all features to eliminate look-ahead bias.
    """
    # Ensure DataFrame is sorted chronologically
    df_sorted = df.sort("timestamp")
    
    features_df = df_sorted.with_columns([
        # Log Returns (shifted by 1)
        (pl.col("close") / pl.col("close").shift(1)).log().shift(1).alias("feature_log_return_1"),
        
        # Exponential Moving Average (shifted by 1)
        pl.col("close").ewm_mean(span=14).shift(1).alias("feature_ema_14"),
        pl.col("close").ewm_mean(span=50).shift(1).alias("feature_ema_50"),
        
        # Volatility / Rolling Standard Deviation (shifted by 1)
        pl.col("close").rolling_std(window_size=20).shift(1).alias("feature_volatility_20"),
        
        # Rolling Z-Score (shifted by 1)
        ((pl.col("close") - pl.col("close").rolling_mean(window_size=20)) / 
         (pl.col("close").rolling_std(window_size=20) + 1e-8)).shift(1).alias("feature_zscore_20"),
    ])
    
    return features_df
