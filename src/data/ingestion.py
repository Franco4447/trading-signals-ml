"""
Data ingestion module for OHLCV data using yfinance or CCXT.
"""
import polars as pl
import yfinance as yf

from src.utils.logger import setup_logger

logger = setup_logger("data_ingestion")

def fetch_ohlcv_yfinance(ticker: str = "BTC-USD", period: str = "1y", interval: str = "1d") -> pl.DataFrame:
    """
    Fetches historical OHLCV data from Yahoo Finance and converts it to Polars DataFrame.
    """
    logger.info(f"Downloading data for {ticker} (period={period}, interval={interval})...")
    data = yf.download(ticker, period=period, interval=interval, progress=False)
    
    if data.empty:
        logger.warning(f"No data returned for ticker {ticker}.")
        return pl.DataFrame()
        
    data = data.reset_index()
    # Flatten MultiIndex columns if present
    if isinstance(data.columns, pl.DataFrame) or hasattr(data.columns, 'levels'):
        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
        
    df = pl.from_pandas(data)
    df = df.rename({
        "Date": "timestamp",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    
    logger.info(f"Successfully fetched {len(df)} rows of data.")
    return df
