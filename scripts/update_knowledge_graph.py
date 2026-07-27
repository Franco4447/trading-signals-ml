"""
MLOps Automation Script: Update Graphify Knowledge Graph.
Extracts AST structure of repository and refreshes .graphify/graph.json.
"""
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from graphify.extractor import extract_repository_graph


def update_graph():
    print(f"Indexando repositorio quantitative AI en '{root_dir}'...")
    graph = extract_repository_graph(root_dir)
    output_path = root_dir / ".graphify" / "graph.json"
    graph.save(output_path)
    
    stats = graph.get_stats()
    print(" Grafo cognitivo Graphify actualizado exitosamente.")
    print(f" Ubicación: {output_path}")
    print(f" Módulos indexados:   {stats['modules']}")
    print(f" Clases detectadas:    {stats['classes']}")
    print(f" Funciones/Métodos:   {stats['functions']}")
    print(f" Aristas de relación: {stats['edges']}")


if __name__ == "__main__":
    update_graph()
