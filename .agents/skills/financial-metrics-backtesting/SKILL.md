---
name: financial-metrics-backtesting
description: Simulación cuantitativa de estrategias en VectorBT/PyBroker con comisiones, slippage y métricas de rendimiento (Sharpe, Sortino, Drawdown).
---

# Financial Metrics & Backtesting Skill

Esta habilidad guía al Agente Backtester en la simulación de ejecuciones financieras con fricciones realistas.

---

## 📊 1. Compendio Teórico de Referencia
Para revisar las ecuaciones del Sharpe Ratio, Sortino Ratio, Max Drawdown y el modelo de fricciones (taker fees + slippage), lee:
- [05. Calibración del Indicador [-1.0, +1.0] y Métricas de Backtesting](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/05_signal_calibration_and_backtesting.md)

---

## 🛠️ 2. Parámetros Obligatorios de Fricción
Todo backtest ejecutado en `src/backtest/` debe incluir explícitamente:
- **Taker Fee ($\phi_{taker}$):** `0.00075` ($0.075\%$)
- **Slippage ($\delta_{slip}$):** `0.0002` ($0.02\%$)

---

## 💻 3. Ejemplo de Cálculo de Métricas en Python

```python
import numpy as np

def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0, periods_per_year: int = 2190) -> float:
    excess_returns = returns - (risk_free_rate / periods_per_year)
    std_dev = np.std(returns)
    if std_dev == 0:
        return 0.0
    return float(np.mean(excess_returns) / std_dev * np.sqrt(periods_per_year))

def calculate_max_drawdown(cum_returns: np.ndarray) -> float:
    peak = np.maximum.accumulate(cum_returns)
    drawdown = (cum_returns - peak) / peak
    return float(np.min(drawdown))
```

---

## 🎯 4. Umbrales Aceptables para Aprobar un Modelo
- **Sharpe Ratio (Neto):** $\ge 1.2$
- **Sortino Ratio (Neto):** $\ge 1.5$
- **Max Drawdown (MDD):** $\le 20.0\%$
