---
name: crypto-microstructure-analysis
description: Ingesta, extracción y análisis de atributos de microestructura en mercados de derivados cripto (Funding Rate, Open Interest, Liquidaciones).
---

# Crypto Microstructure Analysis Skill

Esta habilidad guía al Agente Data Engineer en la extracción de variables explicativas de **microestructura de mercado** para futuros perpetuos cripto.

---

## 📊 1. Compendio Teórico de Referencia
Para comprender las ecuaciones y fundamentos de la tasa de financiación, desequilibrios y liquidaciones, consulta:
- [01. Microestructura de Mercado y Datos Cripto](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/01_market_microstructure_and_crypto.md)

---

## 🛠️ 2. Atributos a Extraer en Polars

1. **Funding Rate Normalizado ($FR_{zscore}$):**
   ```python
   import polars as pl

   def add_funding_rate_features(df: pl.DataFrame) -> pl.DataFrame:
       return df.with_columns([
           # Shift(1) obligatorio para evitar lookahead bias
           pl.col("funding_rate").shift(1).alias("feature_funding_rate"),
           ((pl.col("funding_rate") - pl.col("funding_rate").rolling_mean(window_size=30)) /
            (pl.col("funding_rate").rolling_std(window_size=30) + 1e-8)).shift(1).alias("feature_funding_zscore_30")
       ])
   ```

2. **Divergencia Precio - Interés Abierto ($\Delta P / \Delta OI$):**
   ```python
   def add_open_interest_features(df: pl.DataFrame) -> pl.DataFrame:
       return df.with_columns([
           (pl.col("open_interest").pct_change()).shift(1).alias("feature_oi_pct_change_1"),
           # Variación conjunta de precio e interés abierto
           (pl.col("close").pct_change() * pl.col("open_interest").pct_change()).shift(1).alias("feature_price_oi_product")
       ])
   ```

---

## 🛡️ 3. Reglas de Validación Anti-Leakage
- El valor del *Funding Rate* solo puede asociarse a barras cuyos timestamps sean estrictamente **posteriores** al momento de liquidación de la tasa (típicamente 00:00, 08:00, 16:00 UTC).
- Aplicar siempre `.shift(1)` sobre cualquier serie temporal de microestructura antes de unirla al dataframe de características $X$.
