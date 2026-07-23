# Trading Signals ML 🚀📈

Sistema cuantitativo de Machine Learning de alta precisión diseñado para analizar el comportamiento de mercado de activos cripto (e.g., BTC/USDT) y generar un **indicador de fuerza de señal continuo escalado entre `-1.0` y `+1.0`**.

---

## 💡 Concepto General

El proyecto combina metodologías avanzadas de **Financial Machine Learning** (López de Prado) y procesamiento ultra-rápido vectorized para transformar datos OHLCV en un indicador accionable de compra/venta:

- **`-1.0`**: Venta Fuerte (Strong Sell / Short Max)
- **`0.0`**: Neutral / Fuera del Mercado (Hold)
- **`+1.0`**: Compra Fuerte (Strong Buy / Long Max)

---

## 🛠️ Stack Tecnológico de Vanguardia

- **Data Processing:** `Polars` (Motor vectorized ultra-rápido), `CCXT`, `yfinance`.
- **Machine Learning:** `LightGBM`, `XGBoost`, `Scikit-Learn`, `Optuna` (Tuning hiperparámetros).
- **Etiquetado Cuantitativo:** *Triple Barrier Labeling* (Stop-loss, Take-profit, Time-barrier) y calibración de probabilidades a señal continua.
- **Backtesting & Validation:** `VectorBT` / `PyBroker` con esquema estricto de *Walk-Forward Validation*.
- **Calidad de Código:** `Ruff`, `Pytest`, `Mypy`.
- **Arquitectura de Agentes:** Ecosistema SDD (Spec-Driven Development) gestionado por perfiles en `.agents/`.

---

## ⚡ Inicio Rápido

1. **Clonar e instalar dependencias:**
   ```bash
   git clone https://github.com/Franco4447/trading-signals-ml.git
   cd trading-signals-ml
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Ejecutar Pruebas de Entorno:**
   ```bash
   pytest tests/
   ```

3. **Consultar la Memoria del Proyecto:**
   Para conocer todos los comandos del pipeline, consulta [CLAUDE.md](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/CLAUDE.md).

---

## 📄 Licencia

MIT License — Desarrollado para análisis cuantitativo y generación de señales ML.
