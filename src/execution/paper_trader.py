"""
Paper Trading Dry-Run Engine.
Simulates live signal execution, latency metrics, paper balance tracking, and trade logging.
"""
import time

from src.utils.logger import setup_logger

logger = setup_logger("paper_trader")


class PaperTraderEngine:
    """
    Dry-run simulation engine for live signal testing on Testnet/Paper accounts.
    """
    def __init__(
        self,
        initial_balance: float = 10000.0,
        max_leverage_cap: float = 10.0,
        daily_loss_limit_pct: float = 0.05
    ):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.max_leverage_cap = max_leverage_cap
        self.daily_loss_limit_pct = daily_loss_limit_pct

        self.current_position: dict | None = None
        self.trade_history: list[dict] = []
        self.daily_starting_balance = initial_balance
        self.last_reset_day = time.strftime("%Y-%m-%d")

    def _check_circuit_breakers(self, timestamp: str | None = None) -> bool:
        """
        Enforces Daily Loss Circuit Breaker.
        """
        current_day = timestamp[:10] if (timestamp and len(timestamp) >= 10) else time.strftime("%Y-%m-%d")
        if current_day != self.last_reset_day:
            self.daily_starting_balance = self.balance
            self.last_reset_day = current_day

        daily_loss = (self.daily_starting_balance - self.balance) / self.daily_starting_balance
        if daily_loss >= self.daily_loss_limit_pct:
            logger.error(
                f"CIRCUIT BREAKER TRIGGERED: Daily loss {daily_loss*100:.2f}% "
                f"exceeds limit ({self.daily_loss_limit_pct*100:.2f}%). Signals disabled for 24h."
            )
            return True
        return False

    def process_signal(
        self,
        signal_score: float,
        current_price: float,
        suggested_leverage: float,
        take_profit: float,
        stop_loss: float,
        high: float | None = None,
        low: float | None = None,
        timestamp: str | None = None
    ) -> dict:
        """
        Processes a live signal update and executes virtual paper trades.
        Evaluates bracket TP/SL touches and applies 0.020% Maker Fee on entries and exits.
        """
        start_time = time.perf_counter()

        now_str = timestamp if timestamp else time.strftime("%Y-%m-%d %H:%M:%S")
        if self._check_circuit_breakers(timestamp=timestamp):
            return {
                "status": "BLOCKED_CIRCUIT_BREAKER",
                "balance": self.balance,
                "latency_ms": (time.perf_counter() - start_time) * 1000.0
            }

        # Apply Weekend Liquidity Filter (50% leverage cap reduction on Sat/Sun)
        is_weekend = time.strftime("%w") in ["0", "6"]  # 0=Sunday, 6=Saturday
        weekend_cap = self.max_leverage_cap * 0.50 if is_weekend else self.max_leverage_cap

        # Apply Hard Leverage Cap
        effective_leverage = min(suggested_leverage, weekend_cap)

        target_side = 0
        if signal_score >= 0.3:
            target_side = 1  # Long
        elif signal_score <= -0.3:
            target_side = -1  # Short

        executed_trade = None
        just_closed_by_barrier = False

        # 1. Check Bracket TP/SL touch on existing position before evaluating new signals
        if self.current_position is not None:
            curr_side = self.current_position["side"]
            entry_p = self.current_position["entry_price"]
            pos_size = self.current_position["size"]
            tp_price = self.current_position["take_profit"]
            sl_price = self.current_position["stop_loss"]

            check_high = high if high is not None else current_price
            check_low = low if low is not None else current_price

            closed_reason = None
            exit_price = current_price
            if curr_side == 1:  # Long
                if check_high >= tp_price > 0:
                    closed_reason = "TAKE_PROFIT"
                    exit_price = tp_price
                elif check_low <= sl_price > 0:
                    closed_reason = "STOP_LOSS"
                    exit_price = sl_price
            elif curr_side == -1:  # Short
                if check_low <= tp_price > 0 and tp_price > 0:
                    closed_reason = "TAKE_PROFIT"
                    exit_price = tp_price
                elif check_high >= sl_price > 0 and sl_price > 0:
                    closed_reason = "STOP_LOSS"
                    exit_price = sl_price

            if closed_reason is not None:
                raw_pnl = curr_side * pos_size * ((exit_price - entry_p) / entry_p)
                exit_fee = pos_size * 0.00020  # Maker fee 0.020%
                pnl = raw_pnl - exit_fee
                self.balance += pnl
                executed_trade = {
                    "action": f"CLOSE_{closed_reason}",
                    "side": "LONG" if curr_side == 1 else "SHORT",
                    "exit_price": exit_price,
                    "raw_pnl": raw_pnl,
                    "fee": exit_fee,
                    "pnl": pnl,
                    "new_balance": self.balance,
                    "timestamp": now_str
                }
                self.trade_history.append(executed_trade)
                logger.info(f"Paper Trade Closed ({closed_reason}): PnL=${pnl:.2f} (Fee=${exit_fee:.2f}), Balance=${self.balance:.2f}")
                self.current_position = None
                just_closed_by_barrier = True

        # 2. Handle position management (Pyramiding vs Close vs New)
        if self.current_position is not None:
            curr_side = self.current_position["side"]
            curr_signal = self.current_position.get("last_signal_score", 0.0)

            if target_side != curr_side and target_side != 0:
                # Close existing position on opposite signal
                entry_p = self.current_position["entry_price"]
                pos_size = self.current_position["size"]
                raw_pnl = curr_side * pos_size * ((current_price - entry_p) / entry_p)
                exit_fee = pos_size * 0.00020  # Maker fee 0.020%
                pnl = raw_pnl - exit_fee
                
                self.balance += pnl
                executed_trade = {
                    "action": "CLOSE_SIGNAL",
                    "side": "LONG" if curr_side == 1 else "SHORT",
                    "exit_price": current_price,
                    "raw_pnl": raw_pnl,
                    "fee": exit_fee,
                    "pnl": pnl,
                    "new_balance": self.balance,
                    "timestamp": now_str
                }
                self.trade_history.append(executed_trade)
                logger.info(f"Paper Trade Closed (Opposite Signal): PnL=${pnl:.2f} (Fee=${exit_fee:.2f}), Balance=${self.balance:.2f}")
                self.current_position = None
            
            elif target_side == curr_side and abs(signal_score) > abs(curr_signal) + 0.15:
                # Pyramiding / Position Re-scaling on stronger signal strength
                add_value = self.balance * 0.20 * (effective_leverage / 10.0)
                add_fee = add_value * 0.00020  # Maker fee on addition
                self.balance -= add_fee

                prev_size = self.current_position["size"]
                prev_entry = self.current_position["entry_price"]
                
                # New weighted entry price
                new_size = prev_size + add_value
                new_entry = (prev_size * prev_entry + add_value * current_price) / new_size
                
                # Trailing Stop Loss to Breakeven (Initial Entry Price)
                breakeven_sl = prev_entry

                self.current_position["size"] = new_size
                self.current_position["entry_price"] = new_entry
                self.current_position["stop_loss"] = breakeven_sl
                self.current_position["last_signal_score"] = signal_score
                
                executed_trade = {
                    "action": "PYRAMID_ADD",
                    "side": "LONG" if curr_side == 1 else "SHORT",
                    "add_size": add_value,
                    "fee": add_fee,
                    "new_total_size": new_size,
                    "new_entry_price": new_entry,
                    "trailing_sl_breakeven": breakeven_sl,
                    "timestamp": now_str
                }
                self.trade_history.append(executed_trade)
                logger.info(f"Pyramiding Position Added ({executed_trade['side']}): New Entry=${new_entry:.2f}, Trailing SL=${breakeven_sl:.2f}, Fee=${add_fee:.2f}")

        if target_side != 0 and self.current_position is None and not just_closed_by_barrier:
            # Open new paper position
            position_value = self.balance * (effective_leverage / 10.0)
            entry_fee = position_value * 0.00020  # Maker fee 0.020% on open
            self.balance -= entry_fee
            self.current_position = {
                "side": target_side,
                "entry_price": current_price,
                "leverage": effective_leverage,
                "size": position_value,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "last_signal_score": signal_score,
                "entry_fee": entry_fee,
                "entry_time": now_str
            }
            side_str = "LONG" if target_side == 1 else "SHORT"
            logger.info(f"Paper Trade Opened ({side_str}): Entry=${current_price:.2f}, Size=${position_value:.2f} (Fee=${entry_fee:.2f}), Leverage={effective_leverage:.2f}x (WeekendFilter={is_weekend})")

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "status": "SUCCESS",
            "balance": float(self.balance),
            "position": self.current_position,
            "executed_trade": executed_trade,
            "is_weekend": is_weekend,
            "latency_ms": round(latency_ms, 3)
        }

