---
name: mcp-builder
description: Creación de servidores MCP (Model Context Protocol) en Python para exponer herramientas y señales a clientes externos.
---

# MCP Builder Skill

Esta habilidad guía en la creación de servidores MCP (Model Context Protocol) usando el SDK oficial de Python.

---

## 🛠️ Estructura de un Servidor MCP en Python

```python
from mcp.server.fastmcp import FastMCP
import joblib
import numpy as np

mcp = FastMCP("TradingSignalsEngine")

@mcp.tool()
def predict_signal(symbol: str = "BTC/USDT") -> float:
    """Devuelve la señal actual del indicador escalada en [-1.0, +1.0]."""
    # Lógica de inferencia
    return 0.75

if __name__ == "__main__":
    mcp.run()
```
