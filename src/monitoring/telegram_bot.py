"""
Telegram Bot Notification Module.
Dispatches real-time signal alerts, TP/SL levels, leverage recommendations,
and Circuit Breaker warnings via Telegram Bot API (No-Cost).
"""
import asyncio
import os

import httpx

from src.utils.logger import setup_logger

logger = setup_logger("telegram_bot")


class TelegramNotifier:
    """
    Asynchronous Telegram Notifier for real-time trading signals and risk alerts.
    Gracefully falls back to log-only mode if credentials are not configured.
    """
    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    async def send_message_async(self, message: str) -> bool:
        """
        Sends an asynchronous text message to Telegram.
        """
        if not self.is_configured:
            logger.info(f"[Telegram MOCK Alert]: {message}")
            return True

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(self.api_url, json=payload)
                if response.status_code == 200:
                    logger.info("Telegram notification successfully sent.")
                    return True
                else:
                    logger.error(f"Telegram API error {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Failed to dispatch Telegram message: {e}")
            return False

    def send_signal_alert_sync(
        self,
        symbol: str,
        signal_score: float,
        direction: str,
        recommended_leverage: float,
        take_profit: float,
        stop_loss: float,
        confidence_level: str,
        macro_regime_1d: str = "BULLISH",
        is_pyramid: bool = False
    ) -> bool:
        """
        Formats and dispatches a structured signal alert synchronously.
        Supports Rolling Z-Score Alert evaluation and MTF macro trend context.
        """
        emoji = "🚀" if signal_score >= 0.6 else ("🔻" if signal_score <= -0.6 else "⚖️")
        pyramid_tag = " [PYRAMIDING ADDITION]" if is_pyramid else ""
        msg = (
            f"{emoji} *TRADING SIGNAL ALERT*{pyramid_tag} {emoji}\n\n"
            f"*Asset:* `{symbol}`\n"
            f"*Signal Score:* `{signal_score:+.4f}`\n"
            f"*Macro Trend (1d):* `{macro_regime_1d}`\n"
            f"*Direction:* *{direction}*\n"
            f"*Rec. Leverage (ATR Adjusted):* `{recommended_leverage:.2f}x`\n"
            f"*Take Profit:* `${take_profit:,.2f}`\n"
            f"*Stop Loss:* `${stop_loss:,.2f}`\n"
            f"*Confidence Level:* `{confidence_level}`\n\n"
            f"⚡ _Trading Signals ML Quantitative Engine_"
        )

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.send_message_async(msg))
            return True
        except RuntimeError:
            return asyncio.run(self.send_message_async(msg))

    def send_circuit_breaker_alert_sync(self, reason: str) -> bool:
        """
        Formats and dispatches an emergency circuit breaker alert.
        """
        msg = (
            f"🚨 *HARD CIRCUIT BREAKER TRIGGERED* 🚨\n\n"
            f"*Reason:* {reason}\n"
            f"*Action:* All trading signals halted for 24h protection.\n\n"
            f"⚠️ _Trading Signals ML Risk Protocol_"
        )
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.send_message_async(msg))
            return True
        except RuntimeError:
            return asyncio.run(self.send_message_async(msg))

