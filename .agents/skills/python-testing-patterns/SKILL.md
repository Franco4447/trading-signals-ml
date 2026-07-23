---
name: python-testing-patterns
description: Patrones avanzados para Pytest en proyectos de Machine Learning (fixtures paramétricos, mocks y assert numéricos).
---

# Python Testing Patterns Skill

Patrones avanzados de pruebas unitarias para código cuantitativo en Pytest.

---

## 🧪 Patrones Recomendados

1. **Comparaciones Flotantes (`pytest.approx`):**
   ```python
   import pytest
   
   def test_signal_approx():
       assert signal_value == pytest.approx(0.7, abs=1e-4)
   ```

2. **Fixtures Paramétricos para DataFrames:**
   Utilizar `pytest.fixture` para generar series sintéticas conocidas y verificar que no haya desplazamientos inesperados.
