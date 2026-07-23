---
name: sdd-orchestration
description: Guía e instrucciones para la orquestación de desarrollos basados en especificaciones SDD (Spec-Driven Development) y fundamentación teórica en Trading Signals ML.
---

# SDD Orchestration Skill

Esta habilidad guía al Agente Orquestador en el ciclo de vida de **Spec-Driven Development (SDD)** integrando la base de conocimiento teórica del proyecto.

---

## 📚 1. Vinculación con el Compendio Teórico
Antes de proponer o aprobar una especificación técnica SDD, el Orquestador debe consultar los documentos teóricos correspondientes en `docs/theory/`:

1. **Si el requerimiento involucra Ingesta o Cripto:** Consultar [01. Microestructura de Mercado y Datos Cripto](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/01_market_microstructure_and_crypto.md).
2. **Si involucra Atributos o Polars:** Consultar [02. Estacionariedad y Diferenciación Fraccionaria](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/02_stationarity_and_fracdiff.md).
3. **Si involucra Etiquetado o Modelado ML:** Consultar [03. Etiquetado por Barras Triples y Meta-Etiquetado](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/03_triple_barrier_and_metalabeling.md).
4. **Si involucra Validación o Divisiones Temporales:** Consultar [04. Validación Cruzada Walk-Forward, Purging y Embargo](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/04_walk_forward_purging_embargo.md).
5. **Si involucra Escalado [-1.0, 1.0] o Backtesting:** Consultar [05. Calibración del Indicador [-1.0, +1.0] y Métricas de Backtesting](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/05_signal_calibration_and_backtesting.md).

---

## 📋 2. Proceso SDD

1. **Gatekeeper (Preguntas de Puerta)**: Formular preguntas para aclarar supuestos técnicos.
2. **Documentación SDD**: Escribir la especificación con supuestos anti-leakage y contratos de salida.
3. **Asignación a Subagentes**: Asignar tareas a `data-engineer`, `ml-engineer`, `backtester` y `qa-validator`.
4. **Revisión y OK Cruzado**: Verificar el cumplimiento de los contratos antes del cierre.
