# Plan de Ruta (ROADMAP) — Trading Signals ML

Este documento detalla la hoja de ruta y backlog de desarrollo para la construcción del indicador cuantitativo ML.

---

## 🎯 Fase 1: Infraestructura de Entorno & Agentes SDD (COMPLETADO ✅)
- [x] Configuración del repositorio Git y espacio de trabajo.
- [x] Creación del ecosistema `.agents/` (Orquestador SDD y Agentes Especializados).
- [x] Creación de Skills cuantitativas (`feature-engineering-ml`, `triple-barrier-labeling`, `signal-indicator-scaling`, etc.).
- [x] Definición de `pyproject.toml`, `requirements.txt`, `CLAUDE.md` y `.pre-commit-config.yaml`.

---

## 📊 Fase 2: Ingesta de Datos, Microestructura & Feature Engineering (COMPLETADO ✅)
- [x] Conector `CCXT` y `yfinance` para descarga de velas OHLCV de BTC/USDT.
- [x] Ingesta de Microestructura Cripto (**Funding Rate** y **Open Interest**) en `src/data/ingestion.py`.
- [x] Resampleador a **Barras de Información** (*Dollar Bars* y *Volume Bars*) en `src/data/cleaning.py`.
- [x] Generador de atributos de alto rendimiento en `src/features/technical_indicators.py` usando `Polars`:
  - **Diferenciación Fraccionaria ($d^*$)** con prueba ADF de estacionariedad.
  - Indicadores de Microestructura (Z-Score de Funding Rate y $\Delta P / \Delta OI$).
  - Indicadores de Tendencia (EMA, Volatilidad ATR, Rolling Z-Score).
  - Garantía estricta de cero *look-ahead bias* (`.shift(1)`).

---

## 🧠 Fase 3: Etiquetado, Meta-Labeling & Purged Cross-Validation (COMPLETADO ✅)
- [x] Implementación del etiquetado *Triple Barrier* simétrico en `src/models/triple_barrier.py` (TP, SL por ATR y expiración temporal para Longs y Shorts).
- [x] Algoritmo de **Unicidad de Muestras** de López de Prado para ponderar filas de entrenamiento ($w_t$).
- [x] Pipeline de **Meta-Etiquetado** de 2 etapas con `LightGBM` en `src/models/meta_labeling.py` ($P_{meta} \in [0, 1]$).
- [x] Suite de **Purged Walk-Forward Cross-Validation** con **Embargo** en `src/models/train.py`.
- [x] Escalador de señal continua `src/models/signal_scaler.py` mapeando predicciones a `[-1.0, +1.0]` con Bet Sizing.

---

## 📈 Fase 4: Engine de Backtesting con Apalancamiento & Liquidaciones (COMPLETADO ✅)
- [x] Motor de Backtesting con **Apalancamiento Explícito ($N\text{x}$)** en `src/backtest/engine.py`.
- [x] Simulación de **Precios de Liquidación ($P_{liq}$)** para Longs y Shorts con llamada de margen (pérdida total de posición).
- [x] Deducción de comisiones Taker/Maker sobre el nocional apalancado y penalizaciones de slippage.
- [x] Cálculo de métricas financieras de riesgo: Sharpe Ratio, Sortino Ratio, Profit Factor, Calmar Ratio y Max Drawdown en `src/backtest/metrics.py`.

---

## 🚀 Fase 5: Servidor de Inferencia FastAPI & Detección de Concept Drift (COMPLETADO ✅)
- [x] Servidor **FastAPI** REST (`/predict`, `/health`) para consultas de señal $S_t$, apalancamiento recomendado y TP/SL en `src/api/server.py`.
- [x] Streaming en vivo mediante conexión **WebSocket** (`/ws/signals`).
- [x] Detector de **Concept Drift** con prueba Kolmogorov-Smirnov en `src/monitoring/drift.py` para ajuste automático de riesgo.
