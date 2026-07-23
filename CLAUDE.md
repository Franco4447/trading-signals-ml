# Trading Signals ML — Guía de Desarrollo y Memoria del Código

Guía operativa rápida para desarrolladores y agentes de IA en el repositorio de **`trading-signals-ml`**.

*   **Plan de Ruta y Backlog**: Consulta [ROADMAP.md](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/ROADMAP.md) para ver los hitos y tareas futuras.
*   **Reglas de Workspace y Agentes**: Consulta [.agents/AGENTS.md](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/.agents/AGENTS.md) para ver las directrices de desarrollo de ML.
*   **Compendio Teórico Cuantitativo**: Consulta la carpeta [docs/theory/](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/) para ver la fundamentación matemática del proyecto.

---

## 📚 Compendio Teórico de Referencia (`docs/theory/`)

1. [01. Microestructura de Mercado y Datos Cripto](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/01_market_microstructure_and_crypto.md): Order Book, Information Bars, Funding Rate, Open Interest y Liquidaciones.
2. [02. Estacionariedad y Diferenciación Fraccionaria](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/02_stationarity_and_fracdiff.md): Prueba ADF, retornos logarítmicos, FracDiff ($d^*$) y Rolling Z-Scores.
3. [03. Etiquetado por Barras Triples y Meta-Etiquetado](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/03_triple_barrier_and_metalabeling.md): Take Profit, Stop Loss, Expiración Temporal, Meta-Labeling y Sample Uniqueness.
4. [04. Validación Cruzada Walk-Forward, Purging y Embargo](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/04_walk_forward_purging_embargo.md): Anti-leakage, Purged CV, Embargo y Combinatorial Purged CV (CPCV).
5. [05. Calibración del Indicador [-1.0, +1.0] y Métricas de Backtesting](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/05_signal_calibration_and_backtesting.md): Probabilidades $P_{buy} - P_{sell}$, sigmoide $\tanh$, Sharpe, Sortino, Max Drawdown y fricciones transaccionales.

---

## 🎯 Objetivo del Indicador

El objetivo principal de este sistema de Machine Learning es analizar el comportamiento de un activo cuantitativo (e.g., BTC/USDT en temporalidades de 1h/4h/1d) y generar un **indicador de señal continuo en el rango `[-1.0, +1.0]`**:

| Rango de Señal | Significado Técnico | Acción Sugerida |
| :--- | :--- | :--- |
| **`+0.6` a `+1.0`** | Zona de Compra Fuerte (Strong Buy) | Abrir Posición Long / Acumular |
| **`+0.2` a `+0.6`** | Zona de Compra Moderada (Moderate Buy) | Posición Long ligera |
| **`-0.2` a `+0.2`** | Zona Neutral / Sin Tendencia Clara (Hold) | Mantenerse en Liquidez / Neutral |
| **`-0.6` a `-0.2`** | Zona de Venta Moderada (Moderate Sell) | Reducir Exposición / Short ligero |
| **`-1.0` a `-0.6`** | Zona de Venta Fuerte (Strong Sell) | Abrir Posición Short / Salida Total |

---

## 🚀 Comandos de Uso Frecuente

### 🐍 Entorno Virtual y Dependencias (Python 3.11+)
```bash
# Crear entorno virtual (si no existe)
python -m venv venv

# Activar entorno (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### 🧩 Gestión de Skills de Agente (Vercel Labs / Skills.sh)
```bash
# Buscar nuevas habilidades en el ecosistema (find-skills)
npx skills find [búsqueda]

# Instalar una habilidad desde GitHub
npx skills add vercel-labs/skills@<nombre-skill>
```

### 📊 Ingesta de Datos y Feature Engineering (Polars)
```bash
# Ingesta de OHLCV histórico (CCXT / yfinance)
python -m src.data.ingestion --symbol BTC/USDT --timeframe 4h --days 365

# Procesamiento y cálculo de atributos técnicos (sin lookahead bias)
python -m src.features.technical_indicators --input data/raw/btc_usdt_4h.parquet
```

### 🧠 Entrenamiento de Modelos de ML
```bash
# Etiquetado Triple Barrier y entrenamiento LightGBM / XGBoost
python -m src.models.train --config config/default_config.yaml
```

### 📈 Backtesting y Validación Temporal
```bash
# Ejecutar simulación de estrategia y validación Walk-Forward
python -m src.backtest.engine --model-path models/latest_model.joblib
```

### 🧪 Pruebas Unitarias y Calidad de Código
```bash
# Ejecutar suite de pruebas unitarias y anti-leakage
.\venv\Scripts\python.exe -m pytest tests/

# Linter y Formatter ultra-rápido (Ruff)
.\venv\Scripts\ruff.exe check .
```

---

## 🗄️ Arquitectura del Repositorio

```
trading-signals-ml/
├── .agents/                    # Ecosistema de Agentes y Orquestación SDD
│   ├── AGENTS.md               # Reglas globales del workspace ML
│   ├── profiles/               # Perfiles de Agentes (Orchestrator, Data, ML, Backtest, QA)
│   └── skills/                 # Skills especializadas en ML Cuantitativo (18 habilidades)
├── config/                     # Configuraciones YAML/JSON del activo e hiperparámetros
├── data/                       # Almacenamiento local de Parquet (raw, processed)
├── docs/                       # Documentación técnica, MCPs y especificaciones SDD
│   └── theory/                 # Compendio Teórico Cuantitativo (01 al 05)
├── models/                     # Artefactos de modelos entrenados (.joblib)
├── src/                        # Código fuente modular en Python
│   ├── data/                   # Ingesta y limpieza de series temporales
│   ├── features/               # Ingeniería de atributos con Polars
│   ├── models/                 # Modelos ML, Triple Barrier y Signal Scaler [-1, +1]
│   ├── backtest/               # Motor de backtesting (VectorBT/PyBroker) y métricas
│   └── utils/                  # Logging estructurado y herramientas auxiliar
├── tests/                      # Tests unitarios y comprobación de Data Leakage
├── .pre-commit-config.yaml     # Hooks de pre-commit de Git
├── pyproject.toml              # Configuración de herramientas (Ruff, Pytest)
└── requirements.txt            # Dependencias del proyecto
```
