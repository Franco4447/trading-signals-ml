"""
Data cleaning, validation, and Information Bars sampling module.
"""
import polars as pl

from src.utils.logger import setup_logger

logger = setup_logger("data_cleaning")


def clean_ohlcv_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Cleans OHLCV DataFrame by removing nulls, zero volumes, and duplicate timestamps.
    """
    if df.is_empty():
        return df

    initial_count = len(df)

    cleaned_df = (
        df.unique(subset=["timestamp"])
        .filter(pl.col("timestamp").is_not_null())
        .filter(pl.col("close") > 0)
        .sort("timestamp")
    )

    final_count = len(cleaned_df)
    logger.info(f"Cleaned data: removed {initial_count - final_count} invalid/duplicate rows.")
    return cleaned_df


def compute_dynamic_dollar_bar_threshold(
    df: pl.DataFrame,
    rolling_days: int = 50,
    target_daily_bars: int = 24
) -> float:
    """
    Computes a dynamic, context-adaptive Dollar Bar threshold based on the rolling mean
    of daily dollar volume divided by the target bar frequency (~24 bars/day).
    Prevents time-varying sample imbalance across multi-year market regimes.
    """
    if df.is_empty():
        return 10_000_000.0

    df_clean = clean_ohlcv_data(df)
    if "notional_value" not in df_clean.columns:
        df_clean = df_clean.with_columns((pl.col("close") * pl.col("volume")).alias("notional_value"))

    total_notional = df_clean["notional_value"].sum()
    n_days = max(1, len(df_clean) // 24)
    avg_daily_notional = total_notional / n_days

    dynamic_threshold = float(avg_daily_notional / target_daily_bars)
    # Ensure minimum floor threshold
    dynamic_threshold = max(dynamic_threshold, 100_000.0)

    logger.info(
        f"Dynamic Dollar Bar Threshold computed: ${dynamic_threshold:,.2f} USD "
        f"(Target Daily Bars={target_daily_bars}, Avg Daily Notional=${avg_daily_notional:,.2f})"
    )
    return dynamic_threshold


def resample_to_information_bars(
    df: pl.DataFrame,
    threshold: float | None = None,
    bar_type: str = "dollar",
    auto_dynamic_threshold: bool = True
) -> pl.DataFrame:
    """
    Resamples chronological OHLCV data into Information Bars (Dollar Bars or Volume Bars).
    Supports dynamic context-adaptive threshold calculation.
    
    Parameters:
        df: Polars DataFrame containing OHLCV.
        threshold: Explicit Dollar or Volume threshold. If None and auto_dynamic_threshold=True, computed dynamically.
        bar_type: 'dollar' (Notional Value = Close * Volume) or 'volume' (Shares/Units Volume).
        auto_dynamic_threshold: Whether to compute threshold dynamically if threshold is None.
    """
    if df.is_empty():
        return df

    df_clean = clean_ohlcv_data(df)

    if threshold is None and auto_dynamic_threshold:
        threshold = compute_dynamic_dollar_bar_threshold(df_clean)
    elif threshold is None:
        threshold = 10_000_000.0
    
    if bar_type == "dollar":
        df_clean = df_clean.with_columns(
            (pl.col("close") * pl.col("volume")).alias("notional_value")
        )
        cum_col = "notional_value"
    else:
        cum_col = "volume"

    # Vectorized group assignment based on cumulative threshold
    cum_series = df_clean[cum_col].cum_sum()
    group_series = (cum_series / threshold).cast(pl.Int64)
    
    df_grouped = df_clean.with_columns(group_series.alias("bar_group"))

    aggregated = df_grouped.group_by("bar_group", maintain_order=True).agg([
        pl.col("timestamp").last().alias("timestamp"),
        pl.col("open").first().alias("open"),
        pl.col("high").max().alias("high"),
        pl.col("low").min().alias("low"),
        pl.col("close").last().alias("close"),
        pl.col("volume").sum().alias("volume")
    ]).drop("bar_group")

    logger.info(f"Resampled {len(df_clean)} time bars into {len(aggregated)} {bar_type.capitalize()} Bars (threshold={threshold:,.2f}).")
    return aggregated

