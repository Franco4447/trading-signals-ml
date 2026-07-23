---
name: graphify
description: Indexación de código y documentación en un grafo del conocimiento persistente para trazabilidad de dependencias.
---

# Graphify Skill

Herramienta de análisis del código que construye un grafo con los módulos, funciones y dependencias del repositorio.

---

## 🛠️ Comandos de Uso

```bash
# Extraer el grafo del conocimiento del repositorio
python -m graphify extract .

# Consultar relaciones entre módulos
python -m graphify query "features technical_indicators"
```
