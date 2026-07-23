# Plan de Ruta (ROADMAP) — Trading Signals ML

Este documento detalla la hoja de ruta y backlog de desarrollo para la construcción del indicador cuantitativo ML.

---

## 🎯 Fase 1: Infraestructura de Entorno & Agentes SDD (COMPLETADO ✅)
- [x] Configuración del repositorio Git y espacio de trabajo.
- [x] Creación del ecosistema `.agents/` (Orquestador SDD y 4 Agentes Especializados).
- [x] Creación de Skills cuantitativas (`feature-engineering-ml`, `triple-barrier-labeling`, `signal-indicator-scaling`, etc.).
- [x] Definición de `pyproject.toml`, `requirements.txt`, `CLAUDE.md` y `.pre-commit-config.yaml`.

---

## 📊 Fase 2: Ingesta de Datos & Feature Engineering (EN PROGRESO ⏳)
- [ ] Implementar conector `CCXT` / `yfinance` para descarga de velas OHLCV de BTC/USDT en temporalidades de 1h y 4h.
- [ ] Desarrollar módulo de limpieza e imputación de gaps temporales en `src/data/`.
- [ ] Implementar generador de atributos en `src/features/technical_indicators.py` usando `Polars`:
  - Indicadores de Tendencia (EMA, MACD, ADX).
  - Indicadores de Impulso / Momento (RSI, Stochastic Oscillator).
  - Indicadores de Volatilidad (ATR, Bollinger Bands).
  - Normalización sin *look-ahead bias* (Rolling Z-Score).

---

## 🧠 Fase 3: Etiquetado & Entrenamiento del Modelo ML
- [ ] Implementar etiquetado *Triple Barrier* en `src/models/`:
  - Criterio de barrera vertical (días/barras de expiración).
  - Criterio de barrera horizontal (Take Profit / Stop Loss basado en ATR dinámico).
- [ ] Implementar entrenadores con `LightGBM` y `XGBoost`.
- [ ] Desarrollar el escalador de señal `src/models/signal_scaler.py` para mapear las probabilidades de clase a un número continuo en `[-1.0, +1.0]`.
- [ ] Integrar `Optuna` para ajuste hiperparametral bayesiano.

---

## 📈 Fase 4: Engine de Backtesting & Validación Walk-Forward
- [ ] Integrar `VectorBT` / `PyBroker` en `src/backtest/engine.py`.
- [ ] Implementar simulación de ejecuciones incorporando:
  - Comisiones de exchange (ej. 0.075% taker fee).
  - Slippage realista.
- [ ] Calcular métricas clave: Ratio de Sharpe, Sortino, Profit Factor, Max Drawdown, Calmar Ratio.
- [ ] Implementar suite de validación out-of-sample *Walk-Forward Split*.

---

## 🚀 Fase 5: Monitoreo & Inferencia en Tiempo Real
- [ ] Módulo de inferencia `src/models/predict.py` para consultar en vivo y emitir el score de señal.
- [ ] Exportación de métricas y alertas ante deriva de concepto (*concept drift*).
