---
name: karpathy-guidelines
description: Principios de diseño de Andrej Karpathy: simplicidad radical, inspección de tensores y desarrollo progresivo.
---

# Karpathy Guidelines Skill

Principios fundamentales inspirados en Andrej Karpathy para el diseño de Machine Learning.

---

## 💡 Principios Clave

1. **Become One With The Data:** Inspeccionar manualmente filas de datos, distribuciones de atributos y valores extremos antes de pasar los datos al modelo.
2. **Simple Baseline First:** Iniciar siempre con un modelo de ensamble o regla heurística básica antes de probar arquitecturas complejas.
3. **Verify Tensor Shapes:** Imprimir y verificar las dimensiones de los arreglos ($X.shape, y.shape$) en cada etapa de transformación.
4. **No Premature Abstractions:** Evitar envoltorios (*wrappers*) excesivos que oculten la matemática del pipeline.
