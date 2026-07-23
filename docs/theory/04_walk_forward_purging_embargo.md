# 04. Validación Cruzada Walk-Forward, Purging y Embargo

Este documento presenta la metodología de validación out-of-sample (*fuera de muestra*) requerida para evitar la sobreestimación del rendimiento (*Overfitting / Look-Ahead Bias*) en series temporales financieras.

---

## 1. Por qué la Validación Cruzada K-Fold Tradicional Falla

En conjuntos de datos tabulares (no temporales), la validación cruzada aleatoria K-Fold divide el dataset en $K$ partes aleatorias. Aplicar este enfoque a series temporales financieras es un **error catastrófico**:

1. **Fuga de Información Futuro $\rightarrow$ Pasado:** Al entrenar con observaciones en $t+1$ y probar en $t$, el modelo utiliza información del futuro que aún no ha ocurrido.
2. **Autocorrelación de Muestras:** Como los indicadores y las barras triples abarcan ventanas temporales largas, las variables explicativas en $t$ y $t+1$ son prácticamente idénticas.

---

## 2. Purgado (Purging) y Embargo (Embargo)

Para corregir la fuga de información entre bloques de entrenamiento y prueba, López de Prado introduce dos correcciones obligatorias: **Purged Cross-Validation**.

```
[ ----- TRAIN BLOCK ----- ] [ PURGE ] [ --- TEST BLOCK --- ] [ EMBARGO ] [ ----- TRAIN BLOCK ----- ]
```

### 2.1. Purgado (Purging)
El purgado elimina del conjunto de entrenamiento todas aquellas observaciones cuya etiqueta (Barras Triples) finaliza **después** de que comience el conjunto de prueba.

Sea $t_{train, end}$ el final del conjunto de entrenamiento y $t_{test, start}$ el inicio del conjunto de prueba. Si una etiqueta de entrenamiento fue generada en $t_i < t_{test, start}$ pero su evento finalizó en $\tau_i > t_{test, start}$, esa muestra debe ser **removida por completo de Train**.

### 2.2. Embargo (Embargo)
Como las series financieras presentan autocorrelación serial autorregresiva en las características, se aplica un período de **Embargo** inmediatamente después de finalizar un bloque de Test.

- Se descartan las observaciones de Train que ocurren en el rango $[t_{test, end}, t_{test, end} + h_{embargo}]$.
- Típicamente, el porcentaje de embargo es del $1\%$ al $5\%$ de la longitud total del dataset.

---

## 3. Validación Cruzada Purga Combinatoria (Combinatorial Purged Cross-Validation - CPCV)

Para obtener múltiples rutas de prueba sin romper el orden temporal ni desperdiciar datos históricos, se utiliza **CPCV**:

1. Se divide la serie temporal en $N$ bloques cronológicos contiguos.
2. Se eligen combinaciones de $k$ bloques para formar el grupo de Test, utilizando los restantes $N-k$ bloques para Train.
3. Se aplican Purging y Embargo en los bordes de cada bloque de Test.
4. Permite generar cientos de curvas de patrimonio (*Equity Curves*) sintéticas out-of-sample para calcular la distribución del Sharpe Ratio y evaluar la variabilidad de la estrategia.

---

## 4. Esquema Walk-Forward Secuencial (Walk-Forward Split)

Para la producción continua en `trading-signals-ml`, se utiliza un esquema de **Walk-Forward en Ventana Desplazable** (*Rolling Window*):

```
Step 1: [ Train: 180d ] -> [ Purge ] -> [ Test: 30d ]
Step 2:         [ Train: 180d ] -> [ Purge ] -> [ Test: 30d ]
Step 3:                 [ Train: 180d ] -> [ Purge ] -> [ Test: 30d ]
```

### Invariantes de Ejecución en `src/backtest/`:
- **Cero Fuga en Escaladores:** La media $\mu$ y desviación $\sigma$ empleadas para normalizar $X_{test}$ provienen **exclusivamente** de $X_{train}$. Nunca se calcula el `fit` sobre la totalidad de los datos.
- **Sin Reentrenamiento en el Bloque Test:** El modelo se congela al inicio del bloque de Test de 30 días y realiza inferencia paso a paso.
