---
name: systematic-debugging
description: Metodología de aislamiento de fallos, diagnóstico basado en evidencia de logs y corrección de causa raíz.
---

# Systematic Debugging Skill

Esta habilidad establece el proceso riguroso para investigar y corregir fallos en el pipeline ML.

---

## 🔍 Protocolo de Depuración

1. **Lectura Directa de Logs:** Inspeccionar la traza completa del error (`traceback`) antes de formular cualquier hipótesis.
2. **Reproducción Mínima:** Crear un test aislado en `tests/` que reproduzca el fallo exacto con un mock de datos reducidos.
3. **Identificación de Causa Raíz:** Tracear la causa matemática o de tipo (ej. `NaN` en retornos logarítmicos, índices desalineados).
4. **Sin Parches Superficiales:** Prohibido envolver llamadas fallidas en bloques `try/except` silenciosos o retornar valores por defecto arbitrarios. Corregir el contrato subyacente.
