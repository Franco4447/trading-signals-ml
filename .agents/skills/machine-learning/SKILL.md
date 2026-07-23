---
name: machine-learning
description: Evaluación de curvas de aprendizaje, calibración probabilística y prevención del overfitting en LightGBM y XGBoost.
---

# Machine Learning Skill

Guía práctica de mejores prácticas en Machine Learning supervisado.

---

## 🧠 Directrices de Entorno

1. **Curvas de Aprendizaje:** Graficar la pérdida en Train vs Valid para detectar sobreajuste temprano.
2. **Early Stopping:** Utilizar `early_stopping_rounds=30` en LightGBM para detener el entrenamiento cuando la pérdida fuera de muestra deje de mejorar.
3. **Imputación de Importancia de Features:** Evaluar tanto `split` como `gain` para detectar atributos dominantes espurios.
