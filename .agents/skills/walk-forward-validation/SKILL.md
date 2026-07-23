---
name: walk-forward-validation
description: Directrices para la validación cruzada secuencial Walk-Forward out-of-sample, Purging y Embargo en series temporales financieras.
---

# Walk-Forward Validation Skill

Esta habilidad establece el protocolo estricto para evaluar modelos fuera de muestra (*out-of-sample*) sin contaminación ni fuga de información.

---

## 📊 1. Compendio Teórico de Referencia
Para comprender por qué K-Fold tradicional falla, la teoría del Purgado (Purging), Embargo y la Validación Combinatoria (CPCV), consulta:
- [04. Validación Cruzada Walk-Forward, Purging y Embargo](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/04_walk_forward_purging_embargo.md)

---

## 🔁 2. Configuración de Ventanas Walk-Forward

```
[ Train Window: 180d ] -> [ Purge: 5d ] -> [ Test Window: 30d ] -> [ Embargo: 3d ]
                            ---> Avance de ventana (Step 30d) --->
```

1. **Train Window:** 180 días históricos para ajustar modelos y trasformaciones.
2. **Purge Window:** 5 días para eliminar etiquetas solapadas de Triple Barrier.
3. **Test Window:** 30 días out-of-sample congelados sin reentrenamiento.
4. **Embargo Window:** 3 días al finalizar Test para eliminar la autocorrelación serial antes del siguiente ciclo.

---

## 🛡️ 3. Reglas Invariantes de Código
- `scaler.fit()` debe ejecutarse **exclusivamente sobre Train**. Jamás hacer `fit` sobre la concatenación Train + Test.
- Guardar de forma independiente los resultados y métricas de cada fold out-of-sample para generar la curva de patrimonio acumulada real.
