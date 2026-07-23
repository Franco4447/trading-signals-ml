---
name: test-driven-development
description: Desarrollo guiado por pruebas (TDD) para código cuantitativo y módulos de ML en Python.
---

# Test-Driven Development (TDD) Skill

Esta habilidad establece la disciplina de **Desarrollo Guiado por Pruebas** para el repositorio `trading-signals-ml`.

---

## 🔁 Ciclo TDD (Red -> Green -> Refactor)

1. **Red (Fallo):** Escribir una prueba unitaria en `tests/` que defina el contrato esperado (ej. `test_feature_shift_anti_leakage`) ANTES de escribir el código en `src/`.
2. **Green (Paso):** Escribir la implementación mínima necesaria en `src/` para que la prueba pase.
3. **Refactor:** Limpiar y optimizar el código manteniendo la suite de pruebas 100% en verde.

---

## 🛡️ Regla en ML Cuantitativo
Ninguna función que transforme matrices de datos o genere indicadores de señal debe comitearse sin su correspondiente test unitario en `tests/`.
