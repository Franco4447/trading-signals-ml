# 05. Calibración del Indicador [-1.0, +1.0] y Métricas de Backtesting

Este documento establece las matemáticas del escalado continuo de predicciones y las métricas financieras con fricciones reales que determinan el éxito de la estrategia.

---

## 1. Escalado del Indicador Continuo `[-1.0, +1.0]`

El requisito fundamental de `trading-signals-ml` es entregar una señal flotante unificada $S_t \in [-1.0, +1.0]$.

### 1.1. Mapeo Probabilístico Multiclase
Cuando el modelo clasificador (LightGBM/XGBoost) predice las probabilidades de las 3 clases de Barras Triples:
- $P_{-1} = P(\text{Venta / Stop Loss})$
- $P_0 = P(\text{Neutral / Tiempo Expirado})$
- $P_{+1} = P(\text{Compra / Take Profit})$

La señal escalar $S_t$ se calcula mediante la diferencia directa de las probabilidades extremas:

$$S_t = P_{+1} - P_{-1}$$

#### Propiedades del Mapeo:
- Si el modelo predice $P_{+1} = 0.85, P_{-1} = 0.05 \implies S_t = +0.80$ (Señal de Compra Fuerte).
- Si el modelo predice $P_{+1} = 0.10, P_{-1} = 0.75 \implies S_t = -0.65$ (Señal de Venta Fuerte).
- Si el modelo tiene incertidumbre y asigna $P_0 = 0.80, P_{+1} = 0.10, P_{-1} = 0.10 \implies S_t = 0.0$ (Señal Neutral).

### 1.2. Mapeo Sigmoide desde Modelos de Regresión
Si el modelo estima directamente el retorno esperado $\hat{r}_t$, la señal se escala mediante la función tangente hiperbólica ajustada por la volatilidad local $\sigma_t$:

$$S_t = \tanh\left( \frac{\hat{r}_t}{k \cdot \sigma_t} \right)$$

Donde $k$ es el factor de sensibilidad (típicamente $k \in [1.0, 2.0]$). Para asegurar límites estrictos, el resultado siempre pasa por un operador de recorte:

$$S_t^{clamped} = \text{clip}(S_t, -1.0, +1.0)$$

---

## 2. Fricciones Transaccionales de Mercado

Un backtest que ignora las fricciones es teóricamente nulo. En `src/backtest/engine.py`, todo cambio de posición incurre en dos costos explícitos:

### 2.1. Comisiones por Transacción (Taker / Maker Fees)
- **Taker Fee ($\phi_{taker}$):** Aplicada cuando la orden se ejecuta inmediatamente contra la liquidez del libro (típicamente $0.075\%$ en Binance Futures).
- **Maker Fee ($\phi_{maker}$):** Aplicada cuando la orden aporta liquidez pasiva ($0.02\%$).

### 2.2. Deslizamiento (Slippage)
El deslizamiento $\delta_{slip}$ modela la diferencia entre el precio de la señal $P_t$ y el precio real de ejecución $\tilde{P}_t$ debido a la latencia y la profundidad del libro de órdenes (típicamente $0.02\%$ a $0.05\%$).

### 2.3. Retorno Neto Ajustado por Fricción
Para un cambio de posición $\Delta Pos_t = |Pos_t - Pos_{t-1}|$:

$$R_{net, t} = Pos_{t-1} \cdot R_t - \Delta Pos_t \cdot (\phi_{taker} + \delta_{slip})$$

---

## 3. Métricas Financieras de Desempeño

El éxito del modelo no se mide por Accuracy o ROC-AUC, sino por métricas de rentabilidad ajustadas por riesgo:

### 3.1. Sharpe Ratio Anualizado ($SR$)
$$\text{SR} = \frac{\bar{R}_{net} - R_f}{\sigma_{R_{net}}} \cdot \sqrt{N}$$
Donde $N$ es el número de períodos por año (ej. $N = 365 \times 6 = 2190$ para velas de 4h) y $R_f$ es la tasa libre de riesgo.

### 3.2. Sortino Ratio ($Sortino$)
Calcula el retorno ajustado evaluando **únicamente la volatilidad bajista** ($\sigma_{down}$):

$$\text{Sortino} = \frac{\bar{R}_{net} - R_f}{\sqrt{\frac{1}{M} \sum_{t=1}^M \min(0, R_{net, t})^2}} \cdot \sqrt{N}$$

### 3.3. Max Drawdown ($MDD$)
Mide la máxima caída porcentual desde un pico (*Peak*) hasta un valle (*Trough*) en la curva de capital acumulado $C_t$:

$$\text{MDD} = \max_{\tau \le t} \left( \frac{C_{\tau} - C_t}{C_{\tau}} \right)$$

---

## 4. Umbrales Aceptables para el Proyecto

Para considerar la estrategia lista para ser probada en entornos simulados o en producción, debe cumplir las siguientes condiciones mínimas en el período *Walk-Forward Out-of-Sample*:

| Métrica | Umbral Mínimo Requerido | Valor Objetivo |
| :--- | :--- | :--- |
| **Sharpe Ratio (Neto)** | $> 1.2$ | $> 1.8$ |
| **Sortino Ratio (Neto)** | $> 1.5$ | $> 2.5$ |
| **Max Drawdown (MDD)** | $< 20.0\%$ | $< 12.0\%$ |
| **Profit Factor** | $> 1.3$ | $> 1.6$ |
