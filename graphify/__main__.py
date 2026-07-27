"""
Command-line interface (CLI) entry point for Graphify.
Supports 'extract', 'query', and 'serve' commands.
"""
import argparse
import sys
from pathlib import Path

from graphify.extractor import extract_repository_graph
from graphify.graph import KnowledgeGraph


GRAPH_PATH = Path(".graphify/graph.json")


def main():
    parser = argparse.ArgumentParser(
        description="Graphify: Codebase AST Indexer, Relational Knowledge Graph, and MCP Server."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: extract
    parser_extract = subparsers.add_parser("extract", help="Extract AST knowledge graph from repository")
    parser_extract.add_argument("path", nargs="?", default=".", help="Root directory of repository (default: current directory)")
    parser_extract.add_argument("--output", "-o", default=str(GRAPH_PATH), help="Output JSON graph path")

    # Command: query
    parser_query = subparsers.add_parser("query", help="Query the knowledge graph")
    parser_query.add_argument("term", help="Search term (module name, function, docstring keyword)")
    parser_query.add_argument("--graph", "-g", default=str(GRAPH_PATH), help="Path to stored graph JSON")

    # Command: serve
    subparsers.add_parser("serve", help="Start MCP server in stdio mode for AI agents")

    args = parser.parse_args()

    if args.command == "extract":
        print(f"Indexando repositorio en '{args.path}' mediante análisis AST...")
        graph = extract_repository_graph(args.path)
        graph.save(args.output)
        stats = graph.get_stats()
        print(f" Grafo guardado exitosamente en '{args.output}'.")
        print(f" Resumen: {stats['modules']} módulos | {stats['classes']} clases | {stats['functions']} funciones | {stats['edges']} aristas de relación.")
        sys.exit(0)

    elif args.command == "query":
        graph = KnowledgeGraph.load(args.graph)
        if not graph.nodes:
            print(f" Error: No se encontró un grafo indexado en '{args.graph}'. Ejecute 'python -m graphify extract .' primero.")
            sys.exit(1)

        results = graph.query(args.term)
        print(f"\n### Resultados de búsqueda en Graphify para: '{args.term}' ({len(results)} encontrados)\n")
        for node in results[:20]:  # Limit display to top 20
            print(f"- **[{node['type'].upper()}]** `{node['name']}` (Path: `{node['path']}`)")
            if node.get("docstring"):
                # Clean up docstring single-line display
                short_doc = node["docstring"].strip().split("\n")[0]
                print(f"  > {short_doc}")
            print()
        if len(results) > 20:
            print(f"... y {len(results) - 20} resultados adicionales ocultos.")
        sys.exit(0)

    elif args.command == "serve":
        from graphify.server import run_server
        run_server()

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
