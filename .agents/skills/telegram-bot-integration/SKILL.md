---
name: telegram-bot-integration
description: Guía e instrucciones para la integración de notificaciones push en tiempo real vía Telegram Bot API (No-Cost) en Trading Signals ML.
---

# 📲 Skill: Telegram Bot Integration (`telegram-bot-integration`)

Esta habilidad proporciona el estándar cuantitativo y técnico para configurar, estructurar, formatear y mantener notificaciones push de señales de trading en tiempo real a dispositivos móviles mediante la **Telegram Bot API (Costo $0/mes)**.

---

## 🎯 Requisitos de Credenciales

Para recibir alertas push reales en tu teléfono móvil, se deben definir las siguientes variables de entorno:

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
export TELEGRAM_CHAT_ID="987654321"
```

> [!NOTE]
> **Modo Fallback:** Si las variables no están configuradas, el módulo [src/monitoring/telegram_bot.py](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/src/monitoring/telegram_bot.py) opera en modo *Log-Only* sin bloquear la ejecución ni generar excepciones.

---

## 📜 Estructura Estándar de Alerta de Señal

Toda notificación de señal en vivo debe formatearse en Markdown v2 incluyendo:

1. **Emoji Direccional:** 🚀 para Long, 🔻 para Short, ⚖️ para Neutral.
2. **Identificador del Activo:** (ej. `BTC/USDT`).
3. **Score de Señal $S_t \in [-1.0, +1.0]$:** (ej. `+0.7500`).
4. **Dirección:** (`STRONG_BUY_LONG`, `STRONG_SELL_SHORT`).
5. **Apalancamiento Recomendado:** (ej. `3.75x`).
6. **Niveles Dinámicos TP / SL:** Precios objetivos derivados de la volatilidad ATR local $\sigma_t$.
7. **Nivel de Confianza:** (`HIGH` si $|S_t| \ge 0.60$).

### Ejemplo de Mensaje Generado:
```markdown
🚀 TRADING SIGNAL ALERT 🚀

Asset: BTC/USDT
Signal Score: +0.7500
Direction: STRONG_BUY_LONG
Rec. Leverage: 3.75x
Take Profit: $42,500.00
Stop Loss: $39,200.00
Confidence: HIGH

⚡ Trading Signals ML Quantitative Engine
```

---

## 🚨 Estructura de Alerta de Disyuntor de Emergencia (Circuit Breaker)

Cuando se active el disyuntor de pérdida diaria ($>5\%$) o una alerta de Concept Drift, el bot emite:

```markdown
🚨 HARD CIRCUIT BREAKER TRIGGERED 🚨

Reason: Daily loss threshold (5.0%) reached.
Action: All trading signals halted for protection.

⚠️ Trading Signals ML Risk Protocol
```

---

## 🛠️ Uso en Python (`TelegramNotifier`)

```python
from src.monitoring.telegram_bot import TelegramNotifier

notifier = TelegramNotifier()
notifier.send_signal_alert_sync(
    symbol="BTC/USDT",
    signal_score=0.85,
    direction="STRONG_BUY_LONG",
    recommended_leverage=4.25,
    take_profit=43000.0,
    stop_loss=39500.0,
    confidence_level="HIGH"
)
```
