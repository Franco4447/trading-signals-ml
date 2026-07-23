# Reglas de Desarrollo del Workspace (Workspace Rules)

Este documento define las directrices y estándares del proyecto **`trading-signals-ml`**. Todos los agentes de IA y desarrolladores deben seguir estas reglas rigurosamente.

---

## 📚 Compendio Teórico de Autoridad (`docs/theory/`)
Todo desarrollo o validación impulsada por los agentes debe alinearse con la base de conocimiento teórica del proyecto:
1. [01. Microestructura de Mercado y Datos Cripto](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/01_market_microstructure_and_crypto.md)
2. [02. Estacionariedad y Diferenciación Fraccionaria](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/02_stationarity_and_fracdiff.md)
3. [03. Etiquetado por Barras Triples y Meta-Etiquetado](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/03_triple_barrier_and_metalabeling.md)
4. [04. Validación Cruzada Walk-Forward, Purging y Embargo](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/04_walk_forward_purging_embargo.md)
5. [05. Calibración del Indicador [-1.0, +1.0] y Métricas de Backtesting](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/05_signal_calibration_and_backtesting.md)

---

## 🎨 Principios de Desarrollo en Machine Learning Cuantitativo

### 1. Invariante Antifuga de Datos (*No Look-Ahead Bias / No Data Leakage*)
*   **Prohibición de Datos Futuros:** Ningún cálculo de atributo (feature) o transformación (scaling, normalization, imputación) puede utilizar información de velas o instantes de tiempo posteriores al momento de la predicción ($t > t_0$).
*   **Shift Temporal Obligatorio:** En Polars o Pandas, toda característica técnica generada a partir de precios futuros o retornos proyectados debe aplicar `.shift(1)` o equivalente para asegurar que solo se utilicen observaciones disponibles en $t_0$.
*   **Separación Estricta Train/Test:** La división de datos de entrenamiento y evaluación debe ser puramente cronológica (*Time-Series Split* / *Walk-Forward*). Queda strictly prohibida la validación cruzada aleatoria K-Fold habitual en tabular no temporal.

### 2. Estándar del Indicador de Señal `[-1.0, +1.0]`
*   Todo modelo o ensamble desarrollado en este repositorio debe entregar como producto final un valor flotante escalado en el intervalo continuo **`[-1.0, +1.0]`**.
*   **Mapeo Racional de Salida:**
    - `-1.0` representa la convicción máxima de Venta (Short / Salida).
    - `0.0` representa la postura Neutral / Sin señal clara.
    - `+1.0` representa la convicción máxima de Compra (Long / Entrada).
*   Se prohíbe devolver valores fuera de este rango o métricas no normalizadas directamente como señal de trading.

### 3. Rigor Cuantitativo y Backtesting
*   No evaluar modelos basándose únicamente en métricas tradicionales de ML (como Accuracy o ROC-AUC). La métrica primaria de éxito del indicador incluye **Sharpe Ratio**, **Sortino Ratio** y **Max Drawdown** ajustados por fricciones de mercado.
*   **Fricciones Obligatorias:** Todo backtest realizado en `src/backtest/` debe incluir de manera explícita comisiones por transacción (taker/maker fee) y un margen de slippage.

### 4. Calidad y Tipado de Código
*   Todo el código en `src/` debe contar con anotaciones de tipos (*type hints*) completas.
*   Se requiere que la suite de pruebas `pytest` se mantenga en estado verde antes de dar por completado cualquier ciclo de desarrollo (SDD).

---

## 🤖 Arquitectura del Ecosistema de Agentes

El repositorio utiliza una arquitectura de **5 Agentes Especializados**:

1. **Agente Orquestador SDD (`orchestrator.md`)**: Dirige la planificación mediante SDD, formula preguntas de puerta (Gatekeeper), consulta `docs/theory/` y gestiona las aprobaciones del usuario.
2. **Agente Data Engineer (`data-engineer.md`)**: Maneja ingesta, limpieza, microestructuracripto e indicadores técnicos con Polars sin lookahead bias.
3. **Agente ML Signal Engineer (`ml-engineer.md`)**: Desarrolla Triple Barrier Labeling, Meta-Labeling, modelos LightGBM/XGBoost y la calibración del indicador `[-1.0, +1.0]`.
4. **Agente Backtester & Strategy (`backtester.md`)**: Modela el rendimiento financiero en VectorBT/PyBroker con fricciones y validación Purged Walk-Forward.
5. **Agente QA & Leakage Auditor (`qa-validator.md`)**: Garantiza pruebas unitarias, integridad de datos y ausencia de filtración de información.

---

## 🧰 Catálogo Activo de Skills (`.agents/skills/`)
- **Orquestación y Gestión:** `sdd-orchestration`, `find-skills`, `skill-creator`, `graphify`, `claude-mem`, `mcp-builder`.
- **Ingesta y Features:** `crypto-microstructure-analysis`, `feature-engineering-ml`, `python-performance-optimization`, `context7`.
- **Modelado ML y Señal:** `triple-barrier-labeling`, `signal-indicator-scaling`, `machine-learning`, `karpathy-guidelines`.
- **Backtesting y Validación:** `walk-forward-validation`, `financial-metrics-backtesting`.
- **Auditoría y Pruebas:** `test-driven-development`, `systematic-debugging`, `python-testing-patterns`.
