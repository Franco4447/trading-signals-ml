---
name: triple-barrier-labeling
description: Implementación del método de etiquetado por Barras Triples (López de Prado), Meta-Labeling y Unicidad de Muestras.
---

# Triple Barrier Labeling Skill

Esta habilidad define el procedimiento para generar las etiquetas de entrenamiento ($+1, 0, -1$) considerando el camino continuo del precio y el riesgo de volatilidad.

---

## 📊 1. Compendio Teórico de Referencia
Para consultar las demostraciones de las Barras Triples, la arquitectura de Meta-Etiquetado y la ecuación de pesos por unicidad de muestras, lee:
- [03. Etiquetado por Barras Triples y Meta-Etiquetado](file:///c:/Users/Fmendezcasariego/OneDrive/Carpetas/Desarrollo/trading-signals-ml/docs/theory/03_triple_barrier_and_metalabeling.md)

---

## 🛠️ 2. Parámetros de Etiquetado

1. **Barrera de Take Profit ($\text{pt}$):** $1.5 \times \text{ATR}_{14}$
2. **Barrera de Stop Loss ($\text{sl}$):** $1.0 \times \text{ATR}_{14}$
3. **Barrera Vertical ($H$):** $12$ barras (48 horas en velas de 4h).

---

## 💻 3. Ejemplo de Código en Python

```python
import numpy as np
import pandas as pd

def apply_triple_barrier(prices: pd.Series, atr: pd.Series, pt_mult: float = 1.5, sl_mult: float = 1.0, vertical_bars: int = 12) -> pd.Series:
    labels = pd.Series(index=prices.index, dtype=float)
    
    for i in range(len(prices) - vertical_bars):
        p_curr = prices.iloc[i]
        vol = atr.iloc[i]
        upper = p_curr + (vol * pt_mult)
        lower = p_curr - (vol * sl_mult)
        
        window = prices.iloc[i+1 : i+1+vertical_bars]
        
        touch_upper = window[window >= upper].first_valid_index()
        touch_lower = window[window <= lower].first_valid_index()
        
        if touch_upper is not None and (touch_lower is None or touch_upper < touch_lower):
            labels.iloc[i] = 1.0 # Take Profit
        elif touch_lower is not None and (touch_upper is None or touch_lower < touch_upper):
            labels.iloc[i] = -1.0 # Stop Loss
        else:
            labels.iloc[i] = 0.0 # Time Expiration
            
    return labels
```

---

## 🛡️ 4. Reglas de Validación
- Nunca usar barras fijas en porcentaje (ej. 2% fijo); utilizar siempre volatilidad local ($\text{ATR}$ o $\sigma$).
- Pasar los pesos de unicidad (*sample weights*) al entrenador LightGBM/XGBoost para evitar dar peso excesivo a eventos superpuestos.
