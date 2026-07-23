---
name: feature-engineering-ml
description: Metodología de ingeniería de atributos financieros con Polars garantizando estacionariedad y ausencia de look-ahead bias.
---

# Feature Engineering ML Skill

Esta habilidad define los estándares técnicos para la creación de variables explicativas cuantitativas con **Polars**.

---

## 📊 1. Compendio Teórico de Referencia
Para comprender el dilema entre Estacionariedad y Memoria, la demostración de Diferenciación Fraccionaria y los Z-Scores móviles, consulta:
- [02. Estacionariedad y Diferenciación Fraccionaria](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/02_stationarity_and_fracdiff.md)

---

## 🛡️ 2. Reglas Anti-Leakage e Invariantes
1. **Desfasado explícito (`.shift(1)`)**:
   Toda variable calculada que involucre el precio actual de cierre $C_t$ o el retorno $R_t$ debe ser desplazada para asegurar que en $t$ solo se disponga de datos de $t-1$.
2. **Escalado y Fit Exclusivo en Train**:
   Queda estrictamente prohibido usar `StandardScaler.fit()` o calcular medias/desviaciones estándar globales sobre todo el conjunto de datos.

---

## 🛠️ 3. Patrones de Código en Polars

### Indicadores Técnicos con Shift
```python
import polars as pl

def compute_features(df: pl.DataFrame) -> pl.DataFrame:
    return df.sort("timestamp").with_columns([
        # Log-Returns desfasados
        (pl.col("close") / pl.col("close").shift(1)).log().shift(1).alias("feature_log_return_1"),
        
        # EMAs desfasadas
        pl.col("close").ewm_mean(span=14).shift(1).alias("feature_ema_14"),
        pl.col("close").ewm_mean(span=50).shift(1).alias("feature_ema_50"),
        
        # Volatilidad móvil desfasada
        pl.col("close").rolling_std(window_size=20).shift(1).alias("feature_volatility_20"),
        
        # Rolling Z-Score desfasado
        ((pl.col("close") - pl.col("close").rolling_mean(window_size=20)) / 
         (pl.col("close").rolling_std(window_size=20) + 1e-8)).shift(1).alias("feature_zscore_20"),
    ])
```

---

## 🧪 4. Check-List de Calidad
- [ ] ¿Todas las columnas creadas en `src/features/` inician con el prefijo `feature_`?
- [ ] ¿Se ha verificado mediante prueba unitaria en `tests/test_features.py` que la primera fila no contenga datos de $t$?
- [ ] ¿Pasa la serie de atributos la prueba de estacionariedad (ADF test)?
