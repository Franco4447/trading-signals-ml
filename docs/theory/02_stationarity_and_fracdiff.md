# 02. Estacionariedad y Diferenciación Fraccionaria

Este documento aborda el dilema fundamental del Machine Learning aplicado a series temporales financieras: la tensión entre **Estacionariedad** (necesaria para la capacidad predictiva del modelo) y **Memoria** (necesaria para conservar patrones históricos).

---

## 1. El Dilema Estacionariedad vs. Memoria

Los algoritmos de Machine Learning supervisado (como LightGBM, XGBoost o Redes Neuronales) asumen que los datos de entrada provienen de una distribución de probabilidad estacionaria e idénticamente distribuida (i.i.d.).

### 1.1. No Estacionariedad de los Precios Brutos
Los precios brutos $P_t$ exhiben tendencias de nivel no estacionarias (procesos $I(1)$ o paseos aleatorios):
- La media $E[P_t]$ y la varianza $Var(P_t)$ cambian constantemente a lo largo del tiempo.
- Un árbol de decisión entrenado con $P_t \in [30000, 40000]$ es incapaz de predecir o evaluar observaciones cuando $P_t$ alcanza $\$90,000$, ya que las divisiones de los nodos nunca vieron esos valores numéricos.

### 1.2. El Enfoque Tradicional: Retornos y Diferenciación Entera $d=1$
Para lograr estacionariedad, la práctica habitual consiste en calcular la primera diferencia o retornos logarítmicos:

$$\Delta P_t = P_t - P_{t-1} \quad \text{o} \quad R_t = \ln\left(\frac{P_t}{P_{t-1}}\right)$$

**El Problema:** Al aplicar $d=1$, la serie se vuelve perfectamente estacionaria $I(0)$, pero **se destruye toda la memoria a largo plazo** de la serie. El retorno $R_t$ no contiene información de si el mercado está saliendo de una acumulación de 6 meses o en el pico de una burbuja.

---

## 2. Diferenciación Fraccionaria (Fractional Differentiation)

Marcos López de Prado propone la **Diferenciación Fraccionaria** (*FracDiff*) como una solución matemática para lograr el equilibrio óptimo: remover la tendencia no estacionaria preservando la máxima memoria histórica posible.

### 2.1. Definición Operativa del Operador de Diferencia
Utilizando el operador de retardo (*Backshift Operator*) $B B X_t = X_{t-1}$, una diferencia entera $d$ se define como:

$$(1 - B)^d X_t$$

Extendiendo $d$ a valores reales no enteros $d \in (0, 1)$ mediante la expansión de Binomio de Newton:

$$(1 - B)^d = \sum_{k=0}^{\infty} (-1)^k \binom{d}{k} B^k = 1 - d B + \frac{d(d-1)}{2!} B^2 - \frac{d(d-1)(d-2)}{3!} B^3 + \dots$$

Donde las ponderaciones $\omega_k$ para cada retardo $k$ se calculan recursivamente:

$$\omega_0 = 1$$
$$\omega_k = -\omega_{k-1} \frac{d - k + 1}{k}$$

### 2.2. Valor Fraccionado de la Serie Filtrada
La serie diferenciada fraccionariamente $\tilde{X}_t$ resulta de la convolución ponderada:

$$\tilde{X}_t = \sum_{k=0}^{\infty} \omega_k X_{t-k}$$

En la práctica, la memoria es truncada aplicando un umbral mínimo de peso $\tau$ (ej. $\tau = 1e-4$) para evitar requerir series de tiempo infinitas.

---

## 3. Determinación del exponente óptimo $d^*$

El objetivo es encontrar el valor mínimo de $d \in [0, 1]$ que haga que la serie pase con éxito las pruebas formales de estacionariedad (como la prueba **Augmented Dickey-Fuller - ADF**).

### Protocolo de Selección de $d^*$:
1. Iterar $d$ en el intervalo $[0.0, 1.0]$ con pasos de $0.05$.
2. Para cada $d$, calcular la serie diferenciada $\tilde{P}_t(d)$.
3. Ejecutar la prueba ADF sobre $\tilde{P}_t(d)$ y registrar el valor p ($p\text{-value}$).
4. Calcular el coeficiente de correlación de Pearson o Spearman entre la serie original $P_t$ y $\tilde{P}_t(d)$ para medir la **retención de memoria**.
5. Elegir el menor $d^*$ tal que $p\text{-value} < 0.05$ (rechazo de hipótesis nula de raíz unitaria a 95% de confianza).

```
   p-value ADF
      ^
 1.0  | * (d=0.0 - No Estacionario)
      |   *
      |     *
 0.05 +-------*---------> Umbral de Estacionariedad
      |        *  (d* = 0.35 -> Estacionario con Máxima Memoria)
 0.0  +---------*-----> d
     0.0      d*     1.0
```

---

## 4. Normalización Alternativa: Rolling Z-Scores

Además de FracDiff, se utilizan **Z-Scores Móviles** como técnica de estandarización sin *look-ahead bias*:

$$Z_t = \frac{P_t - \mu_{t-1, w}}{\sigma_{t-1, w}}$$

Donde:
- $\mu_{t-1, w}$ es la media móvil calculada sobre una ventana histórica $w$ que finaliza en $t-1$.
- $\sigma_{t-1, w}$ es la desviación estándar móvil histórica que finaliza en $t-1$.

### Invariante Antifuga:
El cálculo de $\mu$ y $\sigma$ **debe utilizar exclusivamente información hasta $t-1$** (`.shift(1)` en Polars), previniendo que la media o varianza del instante $t$ contamine la variable explicativa.
