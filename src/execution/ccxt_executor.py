"""
CCXT Private API Direct Exchange Execution Adapter.
Supports Binance Futures and Bybit Futures with Testnet / Live key handling.
Enforces Hard Circuit Breakers and Bracket TP/SL Order placement.
"""
import os
from typing import Dict, Optional, Any
import ccxt

from src.utils.logger import setup_logger

logger = setup_logger("ccxt_executor")

HARD_MAX_LEVERAGE = 10.0


class ExchangeExecutor:
    """
    Direct Exchange Execution Adapter connecting to Binance/Bybit Futures APIs.
    """
    def __init__(
        self,
        exchange_id: str = "binance",
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        is_testnet: bool = True
    ):
        self.exchange_id = exchange_id
        self.api_key = api_key or os.getenv("EXCHANGE_API_KEY", "")
        self.secret_key = secret_key or os.getenv("EXCHANGE_API_SECRET", "")
        self.is_testnet = is_testnet

        self.exchange = None
        self._initialize_exchange()

    def _initialize_exchange(self):
        """
        Initializes CCXT private exchange instance with testnet sandbox support.
        """
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            self.exchange = exchange_class({
                "apiKey": self.api_key,
                "secret": self.secret_key,
                "enableRateLimit": True,
                "options": {"defaultType": "future"}
            })

            if self.is_testnet and hasattr(self.exchange, "set_sandbox_mode"):
                self.exchange.set_sandbox_mode(True)
                logger.info(f"CCXT Exchange {self.exchange_id} initialized in TESTNET sandbox mode.")
            else:
                logger.info(f"CCXT Exchange {self.exchange_id} initialized in LIVE production mode.")
        except Exception as e:
            logger.warning(f"Failed to initialize CCXT private exchange ({e}). Operating in Mock Mode.")
            self.exchange = None

    def execute_signal_order(
        self,
        symbol: str,
        signal_score: float,
        current_price: float,
        suggested_leverage: float,
        take_profit: float,
        stop_loss: float,
        order_type: str = "limit",
        position_size_usd: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes leverage configuration, main position order (Maker Limit Order by default),
        and bracket TP/SL orders on the exchange.
        """
        # Hard Circuit Breaker Enforcement
        effective_leverage = min(suggested_leverage, HARD_MAX_LEVERAGE)
        if abs(signal_score) < 0.30:
            logger.info("Signal magnitude below threshold. No order executed.")
            return {"status": "SKIPPED_NEUTRAL"}

        side = "buy" if signal_score >= 0 else "sell"
        position_side = "LONG" if signal_score >= 0 else "SHORT"
        
        # Calculate limit order price for Maker execution (passive liquidity)
        limit_price = current_price * 0.9998 if side == "buy" else current_price * 1.0002

        # Calculate lot size using Fractional Kelly or provided USD size
        if position_size_usd is None:
            from src.models.signal_scaler import calculate_fractional_kelly_bet_size
            kelly_frac = calculate_fractional_kelly_bet_size(win_probability=0.60, win_loss_ratio=1.5, fraction=0.5)
            position_size_usd = 10000.0 * kelly_frac * (effective_leverage / 10.0)

        amount = max(round(position_size_usd / current_price, 6), 0.001)

        logger.info(
            f"Executing {position_side} {order_type.upper()} Order (Maker) on {symbol}: "
            f"LimitPrice=${limit_price:.2f}, Amount={amount} ({symbol.split('/')[0]}), Leverage={effective_leverage:.2f}x, "
            f"TP=${take_profit:.2f}, SL=${stop_loss:.2f}"
        )

        bracket_params = {
            "takeProfit": {"triggerPrice": take_profit},
            "stopLoss": {"triggerPrice": stop_loss}
        }

        if self.exchange is None or not self.api_key:
            # Fallback mock execution for dry-run testing (Maker fee: 0.020%)
            logger.info(f"[Exchange MOCK Limit/Maker Order Executed]: {position_side} {amount} {symbol} @ ${limit_price:.2f} (Maker Fee 0.020%)")
            return {
                "status": "EXECUTED_MOCK_MAKER",
                "symbol": symbol,
                "side": side,
                "order_type": order_type,
                "price": limit_price,
                "amount": amount,
                "maker_fee_pct": 0.00020,
                "effective_leverage": effective_leverage,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "bracket_orders": bracket_params
            }

        try:
            # 1. Set Leverage
            if hasattr(self.exchange, "set_leverage"):
                self.exchange.set_leverage(int(effective_leverage), symbol)

            # 2. Execute Main Limit Order with Bracket TP/SL params
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=limit_price if order_type == "limit" else None,
                params=bracket_params
            )

            logger.info(f"Live Maker Order Executed: Order ID {order.get('id')}")
            return {
                "status": "EXECUTED_LIVE",
                "order_id": order.get("id"),
                "symbol": symbol,
                "side": side,
                "price": order.get("price", limit_price),
                "amount": amount,
                "maker_fee_pct": 0.00020,
                "leverage": effective_leverage,
                "bracket_orders": bracket_params
            }
        except Exception as e:
            logger.error(f"Failed to execute live order on exchange: {e}")
            return {"status": "FAILED", "error": str(e)}

