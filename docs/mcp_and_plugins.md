# Guía de MCPs, Plugins y Hooks en Trading Signals ML

Este documento explica el uso e integración de **Hooks de Git**, **Model Context Protocol (MCP)** y **Plugins** en el repositorio.

---

## 🪝 1. Hooks de Git (Pre-Commit)

El proyecto incluye `.pre-commit-config.yaml` para asegurar la calidad de código antes de cada `git commit`.

### Activación del Hook:
```bash
pip install pre-commit
pre-commit install
```

### Acciones Automatizadas:
- **`ruff`**: Limpieza de sintaxis e importaciones no usadas.
- **`ruff-format`**: Formateo consistente de código Python.
- **`pytest-check`**: Ejecución automática de las pruebas unitarias en `tests/` para impedir la subida de código roto.

---

## 🔌 2. Servidores MCP (Model Context Protocol)

Los servidores MCP permiten a los agentes de IA conectarse con servicios externos de datos financieros y memoria cognitiva.

### MCPs Sugeridos para el Proyecto:
1. **Graphify MCP**: Indexador de memoria cognitiva del código para mantener actualizado el mapa de dependencias del repositorio.
2. **Financial Data MCP (CCXT / Binance API)**: Permite a los agentes consultar precios en tiempo real o libros de órdenes en directo.

### Ejemplo de Configuración (`mcp_config.json`):
```json
{
  "mcpServers": {
    "graphify": {
      "command": "python",
      "args": ["-m", "graphify", "serve"]
    }
  }
}
```

---

## 🧩 3. Plugins y Habilidades

Los agentes de IA en este proyecto operan con las skills ubicadas en `.agents/skills/`:
- `feature-engineering-ml`
- `triple-barrier-labeling`
- `walk-forward-validation`
- `signal-indicator-scaling`
- `sdd-orchestration`
