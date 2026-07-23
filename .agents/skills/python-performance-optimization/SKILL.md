---
name: python-performance-optimization
description: Optimización de rendimiento de procesamiento de datos en Python usando expresiones vectorized de Polars y Numpy.
---

# Python Performance Optimization Skill

Guía para maximizar la velocidad y eficiencia de procesamiento en el pipeline de datos.

---

## ⚡ Reglas de Alto Rendimiento

1. **Evitar bucles `for` sobre DataFrames:** Utilizar siempre expresiones `polars` o vectores `numpy`.
2. **Ejecución Perezosa (`LazyFrame`):** Trabajar con `pl.scan_parquet()` y aplicar `.collect()` únicamente al final de la cadena de transformaciones.
3. **Optimización de Tipos:** Usar `Float32` en lugar de `Float64` si la memoria RAM es un factor crítico durante el entrenamiento.
