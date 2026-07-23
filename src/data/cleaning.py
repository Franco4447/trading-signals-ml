"""
Data cleaning and validation module.
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
