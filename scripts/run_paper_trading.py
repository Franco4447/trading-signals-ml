"""
Live Paper Trading Runner Script.
Executes continuous real-time Paper Trading loop with Multi-Timeframe (MTF) features,
ATR Risk Budgeting leverage, Pyramiding position scaling, and Telegram push alerts.
"""
import argparse
import signal
import sys
import time

import numpy as np
import polars as pl

from src.data.cleaning import compute_dynamic_dollar_bar_threshold, resample_to_information_bars
from src.data.ingestion import fetch_ohlcv_yfinance
from src.execution.paper_trader import PaperTraderEngine
from src.features.technical_indicators import add_multi_timeframe_features
from src.models.signal_scaler import scale_probabilities_to_signal
from src.monitoring.telegram_bot import TelegramNotifier
from src.utils.logger import setup_logger

logger = setup_logger("run_paper_trading")

running = True


def handle_shutdown(signum, frame):
    global running
    logger.info("Shutdown signal received. Exiting Paper Trading loop gracefully...")
    running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def run_loop(symbol: str = "BTC/USDT", interval_sec: int = 10, dry_run_iterations: int = 5):
    logger.info(f"Starting Live Paper Trading Runner for {symbol}...")
    
    paper_trader = PaperTraderEngine(initial_balance=10000.0, max_leverage_cap=10.0, daily_loss_limit_pct=0.05)
    telegram = TelegramNotifier()
    
    iteration = 0
    while running and (dry_run_iterations == 0 or iteration < dry_run_iterations):
        iteration += 1
        logger.info(f"--- Paper Trading Loop Iteration #{iteration} ---")
        
        try:
            # 1. Fetch live multi-timeframe candles
            df_1h = fetch_ohlcv_yfinance(ticker="BTC-USD", period="30d", interval="1h")
            df_1d = fetch_ohlcv_yfinance(ticker="BTC-USD", period="365d", interval="1d")
            
            if df_1h.is_empty():
                logger.warning("No candle data returned. Retrying next cycle...")
                time.sleep(interval_sec)
                continue
            
            # 2. Resample to Dynamic Dollar Bars if applicable
            threshold = compute_dynamic_dollar_bar_threshold(df_1h)
            df_dollar = resample_to_information_bars(df_1h, threshold=threshold)
            
            # 3. Add Multi-Timeframe Features (1d macro trend + 1h baseline)
            df_features = add_multi_timeframe_features(df_1h=df_dollar, df_1d=df_1d)
            
            latest = df_features.tail(1)
            close_price = float(latest["close"][0])
            volatility = float(latest["feature_volatility_20"][0]) if "feature_volatility_20" in latest.columns else close_price * 0.01
            macro_regime = float(latest["feature_macro_regime_1d"][0]) if "feature_macro_regime_1d" in latest.columns else 1.0
            
            # 4. Model Probabilities & Continuous Signal Score
            zscore = float(latest["feature_zscore_20"][0]) if "feature_zscore_20" in latest.columns else 0.0
            prob_buy = float(1.0 / (1.0 + np.exp(-zscore)))
            prob_sell = float(1.0 - prob_buy)
            
            raw_signal = float(scale_probabilities_to_signal(np.array([prob_sell]), np.array([prob_buy]))[0])
            
            # Apply Strict 1d Macro Trend Filter
            signal_score = raw_signal
            if macro_regime < 0 and signal_score > 0:
                logger.info("Macro Trend Filter Active (Bearish 1d): Blocking Long signal.")
                signal_score = 0.0
            elif macro_regime > 0 and signal_score < 0:
                logger.info("Macro Trend Filter Active (Bullish 1d): Blocking Short signal.")
                signal_score = 0.0
                
            # 5. ATR Risk Budgeted Leverage Scaling
            vol_pct = max(volatility / close_price, 0.005)
            target_risk_pct = 0.02
            atr_adjusted_leverage = round(min(target_risk_pct / vol_pct, 10.0) * abs(signal_score), 2)
            
            # 6. Compute TP / SL levels
            tp = close_price + 1.5 * volatility if signal_score >= 0 else close_price - 1.5 * volatility
            sl = close_price - 1.0 * volatility if signal_score >= 0 else close_price + 1.0 * volatility
            
            # 7. Process Paper Signal
            res = paper_trader.process_signal(
                signal_score=signal_score,
                current_price=close_price,
                suggested_leverage=atr_adjusted_leverage,
                take_profit=tp,
                stop_loss=sl
            )
            
            logger.info(f"Signal Result: Score={signal_score:+.4f}, RecLev={atr_adjusted_leverage}x, Status={res.get('status')}, Balance=${res.get('balance'):,.2f}")
            
            # 8. Send Telegram Alert for strong signals
            if abs(signal_score) >= 0.60:
                direction = "STRONG_BUY_LONG" if signal_score >= 0 else "STRONG_SELL_SHORT"
                macro_str = "BULLISH 📈" if macro_regime > 0 else "BEARISH 📉"
                is_pyramid = res.get("executed_trade", {}).get("action") == "PYRAMID_ADD" if res.get("executed_trade") else False
                
                telegram.send_signal_alert_sync(
                    symbol=symbol,
                    signal_score=signal_score,
                    direction=direction,
                    recommended_leverage=atr_adjusted_leverage,
                    take_profit=tp,
                    stop_loss=sl,
                    confidence_level="HIGH",
                    macro_regime_1d=macro_str,
                    is_pyramid=is_pyramid
                )
                
        except Exception as e:
            logger.error(f"Error in Paper Trading loop: {e}", exc_info=True)
            
        if dry_run_iterations == 0:
            time.sleep(interval_sec)

    logger.info("Paper Trading loop completed cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trading Signals ML - Paper Trading Runner")
    parser.add_argument("--symbol", type=str, default="BTC/USDT", help="Trading pair symbol")
    parser.add_argument("--interval", type=int, default=10, help="Loop sleep interval in seconds")
    parser.add_argument("--iterations", type=int, default=5, help="Number of test iterations (0 for infinite)")
    args = parser.parse_args()

    run_loop(symbol=args.symbol, interval_sec=args.interval, dry_run_iterations=args.iterations)
