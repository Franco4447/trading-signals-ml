"""
Triple Barrier Labeling Module (López de Prado Method).
Computes dynamic Take Profit, Stop Loss, and Time Expiration barriers for Longs and Shorts.
"""
import numpy as np
import polars as pl

from src.utils.logger import setup_logger

logger = setup_logger("triple_barrier")


def apply_triple_barrier_labeling(
    df: pl.DataFrame,
    pt_multiplier: float = 1.5,
    sl_multiplier: float = 1.0,
    vertical_barrier_lags: int = 12,
    dynamic_volatility_scaling: bool = True
) -> pl.DataFrame:
    """
    Applies the Triple Barrier Method to create symmetric labels for Long (+1) and Short (-1).
    Supports Dynamic Context-Adaptive Volatility Scaling (scaling TP/SL by short/long vol ratio).
    
    Parameters:
        df: Polars DataFrame containing 'close' and 'feature_volatility_20' (or ATR proxy).
        pt_multiplier: Take Profit ATR multiplier scalar.
        sl_multiplier: Stop Loss ATR multiplier scalar.
        vertical_barrier_lags: Number of max bars allowed before expiration.
        dynamic_volatility_scaling: If True, scales multipliers by local volatility regime.
        
    Returns:
        DataFrame with attached 'label' column in {-1, 0, +1}.
    """
    prices = df["close"].to_numpy()
    volatility = df["feature_volatility_20"].to_numpy() if "feature_volatility_20" in df.columns else prices * 0.01
    volatility = np.where(volatility <= 0, prices * 0.01, volatility)

    if "volatility_1d" in df.columns:
        long_term_vol = df["volatility_1d"].to_numpy()
    else:
        long_term_vol = (
            pl.Series(volatility)
            .rolling_mean(window_size=50)
            .shift(1)
            .fill_null(strategy="forward")
            .fill_null(volatility[0])
            .to_numpy()
        )
    long_term_vol = np.where(long_term_vol <= 0, volatility, long_term_vol)

    n = len(prices)
    labels = np.zeros(n, dtype=int)
    
    for i in range(n - 1):
        p_curr = prices[i]
        vol_curr = volatility[i]
        
        if dynamic_volatility_scaling:
            vol_ratio = vol_curr / (long_term_vol[i] + 1e-8)
            vol_scalar = float(np.clip(vol_ratio, 0.7, 1.8))
        else:
            vol_scalar = 1.0
        
        effective_pt = pt_multiplier * vol_scalar
        effective_sl = sl_multiplier * vol_scalar

        upper_barrier = p_curr + effective_pt * vol_curr
        lower_barrier = p_curr - effective_sl * vol_curr
        
        max_idx = min(i + vertical_barrier_lags, n)
        
        label = 0
        for j in range(i + 1, max_idx):
            p_future = prices[j]
            
            # Check upper barrier (Take Profit for Long / Stop Loss for Short)
            if p_future >= upper_barrier:
                label = +1
                break
            # Check lower barrier (Stop Loss for Long / Take Profit for Short)
            elif p_future <= lower_barrier:
                label = -1
                break
                
        labels[i] = label

    df_labeled = df.with_columns([
        pl.Series("label", labels)
    ])
    
    pos_count = (labels == 1).sum()
    neg_count = (labels == -1).sum()
    zero_count = (labels == 0).sum()
    
    logger.info(f"Triple Barrier Labeling completed (dynamic_vol={dynamic_volatility_scaling}): +1 (Long): {pos_count}, -1 (Short): {neg_count}, 0 (Expired): {zero_count}")
    return df_labeled



def compute_sample_uniqueness_weights(df: pl.DataFrame, vertical_lags: int = 12) -> np.ndarray:
    """
    Computes Sample Uniqueness weights (w_t) according to López de Prado.
    Prevents concurrent overlapping events from over-influencing tree splits.
    """
    n = len(df)
    concurrency = np.ones(n)
    
    # Estimate overlap count
    for i in range(n):
        end_idx = min(i + vertical_lags, n)
        concurrency[i:end_idx] += 1.0

    uniqueness = 1.0 / concurrency
    # Weight is proportional to average uniqueness
    weights = uniqueness / np.mean(uniqueness)
    return weights
