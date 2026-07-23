# 03. Etiquetado por Barras Triples y Meta-Etiquetado

Este documento detalla la metodología cuantitativa de etiquetado (*Labeling*) formulada por Marcos López de Prado. Supera las deficiencias del etiquetado binario tradicional mediante el modelo de **Barras Triples** (*Triple Barrier Method*) y el **Meta-Etiquetado** (*Meta-Labeling*).

---

## 1. Deficiencias del Etiquetado Tradicional

En el Machine Learning ingenuo aplicado a trading, es habitual crear etiquetas binarias basadas en el retorno a $k$ barras futuras:

$$y_t = \begin{cases} 1 & \text{si } P_{t+k} > P_t \\ 0 & \text{en otro caso} \end{cases}$$

### Fallos Fundamentales:
1. **Ignora la trayectoria intra-período:** No evalúa si entre $t$ y $t+k$ el precio cayó un 20% (provocando un Margin Call o un Stop Loss) antes de rebotar.
2. **Horizonte fijo irreal:** No se adapta a regímenes de volatilidad cambiante.
3. **No considera fricciones:** Etiqueta como "positivos" retornos marginales del 0.05% que son consumidos por comisiones y slippage.

---

## 2. El Método de Barras Triples (Triple Barrier Method)

El etiquetado por Barras Triples encierra el camino futuro del precio $P_\tau$ ($\tau > t$) dentro de un rectángulo dinámico definido por tres barreras:

```
        Precio
          ^
          |      +------------------ Take Profit Barrier (pt)
          |     /  \
  P_t ----+----+----+--------------- Vertical Barrier (t + H)
          |        \
          |         +--------------- Stop Loss Barrier (sl)
          +-------------------------> Tiempo (t)
```

### 2.1. Definición de las Barras

1. **Barrera Superior (Take Profit):**
   $$U_t = P_t \cdot (1 + \text{pt} \cdot \sigma_t)$$
2. **Barrera Inferior (Stop Loss):**
   $$L_t = P_t \cdot (1 - \text{sl} \cdot \sigma_t)$$
3. **Barrera Vertical (Tiempo Límite):**
   $$V_t = t + H$$

Donde:
- $\sigma_t$ es la **volatilidad implícita/histórica local** estimada en $t$ (generalmente la media móvil del Average True Range - ATR).
- $\text{pt}$ y $\text{sl}$ son multiplicadores escalares de ganancias y pérdidas (ej. $\text{pt} = 1.5, \text{sl} = 1.0$).
- $H$ es el número máximo de barras horizontales permitidas antes de expirar el evento (ej. $H = 12$ barras de 4h).

### 2.2. Determinación del Primer Contacto (First Touch)
Sea $\tau_{first}$ el primer instante de tiempo en que el precio cruza cualquiera de las tres barreras:

$$\tau_{first} = \min(\tau_{pt}, \tau_{sl}, V_t)$$

La etiqueta categórica asignada $y_t \in \{-1, 0, +1\}$ se define como:

$$y_t = \begin{cases} +1 & \text{si } \tau_{first} = \tau_{pt} \text{ (Toca Take Profit primero)} \\ -1 & \text{si } \tau_{first} = \tau_{sl} \text{ (Toca Stop Loss primero)} \\ 0 & \text{si } \tau_{first} = V_t \text{ (Expira sin tocar Take Profit ni Stop Loss)} \end{cases}$$

---

## 3. Meta-Etiquetado (Meta-Labeling)

El **Meta-Etiquetado** es una arquitectura jerárquica de dos modelos que separa la decisión del *lado de la operación* (Comprar vs. Vender) de la decisión del *tamaño de la posición* (Operar vs. No Operar).

### 3.1. Arquitectura de Dos Pasos:

```
[ Datos / Features ] ---> [ Modelo Primario ] ---> Predicción Lado (Side: +1 / -1)
                                |
                                v
                          [ Meta-Modelo ]  ---> Filtro Confianza (Size: 0 a 1)
```

1. **Modelo Primario (Heurístico / ML Secundario):** Determina el lado de la posición $m_t \in \{-1, +1\}$. Puede ser un modelo simple de medias móviles o un modelo estadístico de baja precisión con alta sensibilidad (High Recall).
2. **Meta-Modelo (ML Principal):** Un modelo binario entrenado para predecir si el Modelo Primario acertará o fallará:
   $$y_{meta, t} = \begin{cases} 1 & \text{si } y_t \cdot m_t > 0 \text{ (El modelo primario acertó el lado y generó ganancia)} \\ 0 & \text{en otro caso (El modelo primario se equivocó)} \end{cases}$$

### 3.2. Beneficios Cuantitativos del Meta-Etiquetado:
- **Reducción masiva de falsos positivos:** Permite filtrar señales débiles o generadas durante fases de alto ruido.
- **Optimización de Posicionamiento:** La salida del Meta-Modelo es una probabilidad $P(\text{Acierto}) \in [0, 1]$, que mapea directamente al tamaño óptimo de la posición (*Bet Sizing*).

---

## 4. Pesos de Muestra e Involucramiento de Información (Sample Uniqueness)

Dado que las Barras Triples pueden durar hasta $H$ períodos, las observaciones consecutivas $t_1, t_2, \dots$ pueden compartir ventanas temporales superpuestas.

### Unicidad Promedio de una Muestra ($\bar{u}_t$):
Para cada instante $t$, se calcula cuántos otros eventos concurrentes estaban activos en el mismo momento. Si una barra coincide con otras $N$ posiciones activas, la información compartida reduce su unicidad a $1/N$.

Al entrenar LightGBM / XGBoost, se asigna a cada fila $t$ un **peso de muestra** $w_t = \bar{u}_t \cdot |R_t|$, asegurando que las observaciones altamente independientes y de mayor retorno relativo tengan mayor impacto en la optimización del árbol.
