# 01. Microestructura de Mercado y Datos Cripto

Este documento establece el marco teórico y matemático sobre cómo se forman los precios en los mercados financieros, con especial énfasis en el mercado de derivados de criptomonedas (Contratos Perpetuos).

---

## 1. Formación de Precios y Libro de Órdenes (Order Book)

El precio en cualquier mercado líquido no es una entidad abstracta, sino el resultado continuo del cruce entre **órdenes limitadas** (*Limit Orders*) y **órdenes a mercado** (*Market Orders*).

### 1.1. El Libro de Órdenes (Order Book)
El libro de órdenes se compone de dos lados:
- **Bids (Ofertas de Compra):** Compradores dispuestos a adquirir la moneda a un precio máximo $P_{bid}$. La mejor oferta es $P_{bid, max}$.
- **Asks (Ofertas de Venta):** Vendedores dispuestos a entregar la moneda a un precio mínimo $P_{ask}$. La mejor demanda es $P_{ask, min}$.
- **Spread Bid-Ask:** Es el margen entre el mejor ask y el mejor bid:
  $$S = P_{ask, min} - P_{bid, max}$$

### 1.2. Tipos de Muestreo de Datos: Time Bars vs Information-Driven Bars
Tradicionalmente, las series de tiempo financieras se muestrean a intervalos cronológicos fijos (e.g., velas de 1 minuto, 1 hora, 4 horas). Sin embargo, Marcos López de Prado (*Advances in Financial Machine Learning*) demuestra que las velas cronológicas violan supuestos estadísticos clave:

1. **Heterocedasticidad:** El volumen y la volatilidad varían enormemente durante el día.
2. **No-Normalidad:** Las rentabilidades muestreadas por tiempo exhiben colas pesadas (*heavy tails*) y kurtosis elevada.

#### Barras Alternativas Recomendadas:
- **Volume Bars:** Se genera una nueva barra cada vez que se negocia una cantidad predefinida de unidades del activo $V_{target}$ (ej. 1,000 BTC).
- **Dollar / Notional Bars:** Se genera una nueva barra cada vez que el valor nocional transferido alcanza $N_{target}$ (ej. $10,000,000 USD).
- **Information Bars (Tick/Volume Imbalance Bars):** Capturan el desequilibrio entre compradores y vendedores agresivos, muestreando cuando el flujo de órdenes informadas supera el umbral esperado.

---

## 2. Microestructura de Derivados Cripto (Perpetual Swaps)

Los contratos de futuros perpetuos (*Perpetuals*) no tienen fecha de vencimiento. Para mantener el precio del futuro ($P_{perpetual}$) anclado al precio del mercado al contado ($P_{spot}$), los exchanges utilizan el mecanismo de **Funding Rate** (Tasa de Financiación).

### 2.1. Funding Rate (Tasa de Financiación)
La tasa de financiación es un pago periódico entre traders en posición Long y Short (típicamente cada 8 horas):

$$\text{Funding Rate} = \text{Premium Index} + \text{clamp}(\text{Interest Rate} - \text{Premium Index}, -0.05\%, +0.05\%)$$

Donde el Premium Index mide la desviación entre el contrato perpetuo y el índice Spot:
$$\text{Premium Index} = \frac{\max(0, P_{bid, impact} - P_{spot}) - \max(0, P_{spot} - P_{ask, impact})}{P_{spot}}$$

#### Interpretación Cuantitativa:
- **Funding Rate Positivo ($>0$):** Los traders Long pagan a los Short. Muestra euforia compradora. Si el Funding Rate es desproporcionadamente alto ($>0.05\%$), el mercado está sobre-apalancado en Long, aumentando la probabilidad de una **cascada de liquidaciones (Long Squeeze)**.
- **Funding Rate Negativo ($<0$):** Los traders Short pagan a los Long. Muestra presión bajista o pánico. Un Funding Rate fuertemente negativo ($<-0.05\%$) sugiere riesgo de **Short Squeeze**.

### 2.2. Interés Abierto (Open Interest - OI)
El *Open Interest* representa el número total de contratos derivados abiertos que no han sido liquidados ni cerrados.

- **$\Delta P > 0$ y $\Delta OI > 0$:** Entrada de nuevo capital en posición Long. Tendencia alcista fuerte y respaldada.
- **$\Delta P > 0$ y $\Delta OI < 0$:** Cobertura de posiciones Short (*Short Covering*). Subida de precio frágil impulsada por cierre de ventas, no por nueva compra.
- **$\Delta P < 0$ y $\Delta OI > 0$:** Entrada de nuevo capital en posición Short. Tendencia bajista fuerte y respaldada.
- **$\Delta P < 0$ y $\Delta OI < 0$:** Cierre de posiciones Long (*Long Unwinding*). Caída impulsada por toma de ganancias o stop losses de compradores.

### 2.3. Volatilidad de Liquidaciones y Cascadas
Cuando el precio cruza el precio de liquidación de un trader apalancado, el exchange ejecuta automáticamente una orden a mercado para cerrar la posición:
- Una liquidación Long genera una **orden de Venta a mercado**.
- Una liquidación Short genera una **orden de Compra a mercado**.

En momentos de alto apalancamiento, las liquidaciones desencadenan una reacción en cadena (efecto dominó) que provoca mechas extremas en el precio.

---

## 3. Implicaciones para la Estrategia de Machine Learning

En `trading-signals-ml`, las métricas de microestructura cripto actúan como **variables explicativas exógenas líderes**:

1. **Filtro de Exposición en Zonas de Riesgo:** Cuando el Funding Rate alcanza percentiles extremos ($>95\%$ histórico), el modelo debe calibrar las probabilidades hacia neutralidad o venta ($Signal \rightarrow -1.0$), evitando abrir posiciones Long en techos de apalancamiento.
2. **Divergencias Precio-OI:** Integrar la relación $\Delta P / \Delta OI$ como atributo normalizado en Polars permite al modelo diferenciar tendencias sostenibles de impulsos especulativos de corto plazo.
