"""
Unit tests for Telegram Bot Notification Module.
Verifies message formatting, mock fallback, and signal/circuit breaker alerts.
"""
from src.monitoring.telegram_bot import TelegramNotifier


def test_telegram_notifier_unconfigured_fallback():
    # Test graceful fallback when bot_token and chat_id are not provided
    notifier = TelegramNotifier(bot_token=None, chat_id=None)
    assert not notifier.is_configured

    # Test sync dispatch in log-only mock mode
    res = notifier.send_signal_alert_sync(
        symbol="BTC/USDT",
        signal_score=0.85,
        direction="STRONG_BUY_LONG",
        recommended_leverage=4.25,
        take_profit=42500.0,
        stop_loss=39200.0,
        confidence_level="HIGH"
    )
    assert res is True


def test_telegram_notifier_circuit_breaker_alert():
    notifier = TelegramNotifier(bot_token=None, chat_id=None)
    res = notifier.send_circuit_breaker_alert_sync("Daily loss limit exceeded (5.0%)")
    assert res is True
