"""
MCP (Model Context Protocol) Server for Graphify.
Exposes AST code indexer, query search, and dependency tools to AI agents
using FastMCP (if available) or lightweight stdio JSON-RPC fallback.
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from graphify.extractor import extract_repository_graph
from graphify.graph import KnowledgeGraph


GRAPH_PATH = Path(".graphify/graph.json")


def _tool_extract(directory: str = ".") -> str:
    """Regenera el grafo cognitivo del repositorio analizando los archivos Python por AST."""
    graph = extract_repository_graph(directory)
    graph.save(GRAPH_PATH)
    stats = graph.get_stats()
    return f"Grafo extraído y guardado exitosamente: {stats['modules']} módulos, {stats['classes']} clases, {stats['functions']} funciones, {stats['edges']} aristas."


def _tool_query(query_string: str) -> List[Dict[str, Any]]:
    """Busca en el grafo del conocimiento nodos coincidentes en nombre, ruta o docstring."""
    graph = KnowledgeGraph.load(GRAPH_PATH)
    return graph.query(query_string)[:25]


def _tool_dependencies(module_name: str) -> List[str]:
    """Lista qué módulos y librerías son importados (dependencias directas) por un archivo o módulo."""
    graph = KnowledgeGraph.load(GRAPH_PATH)
    return graph.get_dependencies(module_name)


def _tool_dependents(module_name: str) -> List[str]:
    """Lista qué archivos y módulos del proyecto dependen de un módulo dado (dependientes inversos)."""
    graph = KnowledgeGraph.load(GRAPH_PATH)
    return graph.get_dependents(module_name)


try:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("GraphifyEngine")

    @mcp.tool()
    def graphify_extract(directory: str = ".") -> str:
        """Regenerate the repository AST knowledge graph."""
        return _tool_extract(directory)

    @mcp.tool()
    def graphify_query(query_string: str) -> List[Dict[str, Any]]:
        """Search the repository graph by term or keyword."""
        return _tool_query(query_string)

    @mcp.tool()
    def graphify_dependencies(module_name: str) -> List[str]:
        """List internal modules imported by the specified module."""
        return _tool_dependencies(module_name)

    @mcp.tool()
    def graphify_dependents(module_name: str) -> List[str]:
        """List internal modules that import the specified module."""
        return _tool_dependents(module_name)

    def run_server():
        mcp.run()

except ImportError:
    # Lightweight stdio JSON-RPC fallback if official mcp SDK is not installed in venv
    def run_server():
        print("Starting Graphify lightweight stdio JSON-RPC MCP server...", file=sys.stderr)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                req_id = req.get("id")
                method = req.get("method")
                params = req.get("params", {})

                if method == "tools/list":
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "tools": [
                                {"name": "graphify_extract", "description": "Regenerate repository AST knowledge graph"},
                                {"name": "graphify_query", "description": "Search the repository graph by term"},
                                {"name": "graphify_dependencies", "description": "List internal modules imported by target module"},
                                {"name": "graphify_dependents", "description": "List internal modules that import target module"}
                            ]
                        }
                    }
                elif method == "tools/call":
                    t_name = params.get("name")
                    t_args = params.get("arguments", {})
                    if t_name == "graphify_extract":
                        out = _tool_extract(t_args.get("directory", "."))
                    elif t_name == "graphify_query":
                        out = _tool_query(t_args.get("query_string", ""))
                    elif t_name == "graphify_dependencies":
                        out = _tool_dependencies(t_args.get("module_name", ""))
                    elif t_name == "graphify_dependents":
                        out = _tool_dependents(t_args.get("module_name", ""))
                    else:
                        out = f"Unknown tool: {t_name}"

                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False)}]}
                    }
                else:
                    res = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

                print(json.dumps(res), flush=True)
            except Exception as e:
                err_res = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
                print(json.dumps(err_res), flush=True)
