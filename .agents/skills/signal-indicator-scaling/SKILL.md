---
name: signal-indicator-scaling
description: Algoritmos para calibración y escalado de salidas probabilísticas o de regresión a la señal continua unificada [-1.0, +1.0].
---

# Signal Indicator Scaling Skill

Esta habilidad establece las fórmulas de calibración para transformar las salidas de los modelos de ML en un indicador continuo estandarizado en el rango **`[-1.0, +1.0]`**.

---

## 📊 1. Compendio Teórico de Referencia
Para revisar las justificaciones matemáticas del mapeo de probabilidades bayesianas y la sigmoide $\tanh$, consulta:
- [05. Calibración del Indicador [-1.0, +1.0] y Métricas de Backtesting](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/05_signal_calibration_and_backtesting.md)

---

## 🧮 2. Métodos de Escalado en `src/models/signal_scaler.py`

### 2.1. Diferencia de Probabilidades Multiclase ($P_{buy} - P_{sell}$)
```python
import numpy as np

def scale_probabilities_to_signal(prob_sell: np.ndarray, prob_buy: np.ndarray) -> np.ndarray:
    """
    Entrada: Probabilidades de clase de Venta (P_-1) y Compra (P_+1).
    Salida: Flotante continuo en [-1.0, +1.0].
    """
    raw_signal = prob_buy - prob_sell
    return np.clip(raw_signal, -1.0, 1.0)
```

### 2.2. Tangente Hiperbólica Ajustada por Volatilidad
```python
def scale_regression_return_to_signal(predicted_returns: np.ndarray, volatility: np.ndarray, factor: float = 1.5) -> np.ndarray:
    """
    Entrada: Retornos esperados continuos y volatilidad local.
    Salida: Flotante continuo en [-1.0, +1.0].
    """
    safe_vol = np.where(volatility <= 0, 1e-6, volatility)
    normalized = predicted_returns / (factor * safe_vol)
    return np.clip(np.tanh(normalized), -1.0, 1.0)
```

---

## 🛡️ 3. Regla de Oro
- Todo módulo o subagente que genere señales finales **debe aplicar `np.clip(signal, -1.0, 1.0)`** para certificar que ningún número flotante se desvíe del contrato del workspace.
