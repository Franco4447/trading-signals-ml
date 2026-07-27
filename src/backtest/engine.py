"""
Vectorized & Event-Driven Backtesting Engine.
Simulates explicit Leverage (Nx), Margin Maintenance, Liquidation Prices (P_liq),
Taker/Maker fees on notional value, and slippage.
"""

import numpy as np
import polars as pl

from src.backtest.metrics import (
    calculate_calmar_ratio,
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
)
from src.utils.logger import setup_logger

logger = setup_logger("backtest_engine")


def run_leverage_backtest(
    df: pl.DataFrame,
    signal_col: str = "signal",
    price_col: str = "close",
    high_col: str = "high",
    low_col: str = "low",
    leverage: float = 3.0,
    signal_threshold: float = 0.3,
    taker_fee: float = 0.00075,
    slippage: float = 0.0002,
    maintenance_margin_rate: float = 0.005,
    initial_capital: float = 10000.0
) -> dict:
    """
    Executes vectorized backtest from continuous signal [-1.0, +1.0] with explicit Leverage and Liquidation simulation.
    
    Parameters:
        df: Polars DataFrame containing prices.
        leverage: Max leverage multiplier (e.g., 3.0x, 5.0x, 10.0x).
        signal_threshold: Minimum absolute signal magnitude to open position.
        taker_fee: Fee charged on NOTIONAL trade volume.
        slippage: Execution price slippage penalty.
        maintenance_margin_rate: Exchange Maintenance Margin Rate (MMR).
        initial_capital: Starting portfolio balance in USDT.
    """
    prices = df[price_col].to_numpy()
    highs = df[high_col].to_numpy() if high_col in df.columns else prices
    lows = df[low_col].to_numpy() if low_col in df.columns else prices
    signals = df[signal_col].to_numpy()
    
    n = len(prices)
    if n < 2:
        return {"total_return": 0.0, "sharpe_ratio": 0.0, "max_drawdown": 0.0}

    capital = initial_capital
    equity_curve = [capital]
    returns_list = []
    
    pos_side = 0.0  # -1.0 (Short), 0.0 (Liquidity), +1.0 (Long)
    entry_price = 0.0
    liquidation_price = 0.0
    position_notional = 0.0
    
    liquidations_count = 0
    total_trades = 0

    for i in range(1, n):
        p_prev = prices[i - 1]
        p_curr = prices[i]
        h_curr = highs[i]
        l_curr = lows[i]
        sig_prev = signals[i - 1]
        
        # 1. Check liquidation for active position during current bar
        liquidated = False
        if pos_side > 0:  # Long
            if l_curr <= liquidation_price:
                # Long Liquidation: Loss of entire position margin
                capital -= position_notional / leverage
                capital = max(capital, 1e-4)
                pos_side = 0.0
                liquidated = True
                liquidations_count += 1
                logger.warning(f"Bar {i}: Long Liquidation triggered at Low={l_curr:.2f} (P_liq={liquidation_price:.2f}).")
        elif pos_side < 0:  # Short
            if h_curr >= liquidation_price:
                # Short Liquidation: Loss of entire position margin
                capital -= position_notional / leverage
                capital = max(capital, 1e-4)
                pos_side = 0.0
                liquidated = True
                liquidations_count += 1
                logger.warning(f"Bar {i}: Short Liquidation triggered at High={h_curr:.2f} (P_liq={liquidation_price:.2f}).")

        # 2. Compute Return on active non-liquidated position
        if pos_side != 0.0 and not liquidated:
            p_return = (p_curr - p_prev) / p_prev
            pnl = pos_side * position_notional * p_return
            capital += pnl

        # 3. Position Sizing & Rebalancing based on new signal
        target_side = 0.0
        if abs(sig_prev) >= signal_threshold:
            target_side = np.sign(sig_prev) * min(abs(sig_prev), 1.0)

        # Execute Trade if position side changes
        if target_side != pos_side and not liquidated:
            # Fee charged on total notional turnover
            turnover_notional = abs(target_side - pos_side) * capital * leverage
            friction = turnover_notional * (taker_fee + slippage)
            capital -= friction
            capital = max(capital, 1e-4)
            
            pos_side = np.sign(target_side)
            if pos_side != 0.0:
                total_trades += 1
                entry_price = p_curr
                position_notional = capital * leverage * abs(target_side)
                
                # Calculate exact Exchange Liquidation Price
                if pos_side > 0:  # Long
                    liquidation_price = entry_price * (1.0 - (1.0 / leverage) + maintenance_margin_rate)
                else:  # Short
                    liquidation_price = entry_price * (1.0 + (1.0 / leverage) - maintenance_margin_rate)
            else:
                position_notional = 0.0
                liquidation_price = 0.0

        bar_return = (capital - equity_curve[-1]) / equity_curve[-1]
        returns_list.append(bar_return)
        equity_curve.append(capital)

    returns_arr = np.array(returns_list)
    cum_returns = np.array(equity_curve) / initial_capital

    sharpe = calculate_sharpe_ratio(returns_arr)
    sortino = calculate_sortino_ratio(returns_arr)
    max_dd = calculate_max_drawdown(cum_returns)
    profit_factor = calculate_profit_factor(returns_arr)
    calmar = calculate_calmar_ratio(cum_returns)

    total_return = (capital - initial_capital) / initial_capital
    logger.info(
        f"Leverage Backtest ({leverage}x) Completed. Return: {total_return*100:.2f}%, "
        f"Sharpe: {sharpe:.2f}, Sortino: {sortino:.2f}, Max DD: {max_dd*100:.2f}%, Liquidations: {liquidations_count}"
    )

    return {
        "total_return": float(total_return),
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "max_drawdown": float(max_dd),
        "profit_factor": float(profit_factor),
        "calmar_ratio": float(calmar),
        "liquidations_count": liquidations_count,
        "total_trades": total_trades,
        "final_capital": float(capital),
        "cum_returns": cum_returns,
        "returns": returns_arr
    }
