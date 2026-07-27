"""
Knowledge Graph data structure and relational query engine for Graphify.
Stores AST nodes (modules, classes, functions) and directed edges (imports, defines, inherits),
with persistence to JSON and query capabilities.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class KnowledgeGraph:
    """
    In-memory graph database and JSON serializer for code repository structure.
    """
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, str]] = []
        self._out_edges: Dict[str, List[Dict[str, str]]] = {}
        self._in_edges: Dict[str, List[Dict[str, str]]] = {}

    def add_node(self, node_id: str, node_type: str, name: str, path: str, docstring: Optional[str] = None, **kwargs) -> None:
        """
        Adds or updates a node in the graph.
        """
        self.nodes[node_id] = {
            "id": node_id,
            "type": node_type,  # 'module', 'class', 'function'
            "name": name,
            "path": path,
            "docstring": docstring or "",
            **kwargs
        }
        if node_id not in self._out_edges:
            self._out_edges[node_id] = []
        if node_id not in self._in_edges:
            self._in_edges[node_id] = []

    def add_edge(self, source: str, target: str, relation: str = "imports") -> None:
        """
        Adds a directed edge between two nodes.
        """
        edge = {"source": source, "target": target, "relation": relation}
        # Avoid duplicate edges
        if edge not in self.edges:
            self.edges.append(edge)
            if source not in self._out_edges:
                self._out_edges[source] = []
            if target not in self._in_edges:
                self._in_edges[target] = []
            self._out_edges[source].append(edge)
            self._in_edges[target].append(edge)

    def save(self, filepath: str | Path) -> None:
        """
        Persists the graph to a JSON file.
        """
        path_obj = Path(filepath)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "nodes": self.nodes,
            "edges": self.edges
        }
        with open(path_obj, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: str | Path) -> "KnowledgeGraph":
        """
        Loads a graph from a JSON file.
        """
        graph = cls()
        path_obj = Path(filepath)
        if not path_obj.exists():
            return graph

        with open(path_obj, "r", encoding="utf-8") as f:
            data = json.load(f)

        for node_id, attrs in data.get("nodes", {}).items():
            graph.nodes[node_id] = attrs
            graph._out_edges[node_id] = []
            graph._in_edges[node_id] = []

        for edge in data.get("edges", []):
            graph.add_edge(edge["source"], edge["target"], edge.get("relation", "imports"))

        return graph

    def query(self, query_string: str) -> List[Dict[str, Any]]:
        """
        Searches nodes by matching query terms against node ID, name, path, or docstring.
        """
        if not query_string or not query_string.strip():
            return []

        terms = [t.lower() for t in query_string.strip().split()]
        results = []

        for node in self.nodes.values():
            searchable_text = f"{node['id']} {node['name']} {node['path']} {node.get('docstring', '')}".lower()
            if all(term in searchable_text for term in terms):
                results.append(node)

        return results

    def get_dependencies(self, module_query: str) -> List[str]:
        """
        Returns a list of module IDs imported by the given module.
        """
        target_id = self._resolve_module_id(module_query)
        if not target_id:
            return []

        deps: Set[str] = set()
        for edge in self._out_edges.get(target_id, []):
            if edge["relation"] == "imports":
                deps.add(edge["target"])
        return sorted(list(deps))

    def get_dependents(self, module_query: str) -> List[str]:
        """
        Returns a list of module IDs that import the given module.
        """
        target_id = self._resolve_module_id(module_query)
        if not target_id:
            return []

        dependents: Set[str] = set()
        for edge in self._in_edges.get(target_id, []):
            if edge["relation"] == "imports":
                dependents.add(edge["source"])
        return sorted(list(dependents))

    def _resolve_module_id(self, query: str) -> Optional[str]:
        """
        Resolves a module name, path, or ID to a valid node ID in the graph.
        """
        if query in self.nodes and self.nodes[query].get("type") == "module":
            return query
        q_clean = query.replace("\\", "/").replace(".py", "").replace("/", ".").strip(".")
        for node_id, node in self.nodes.items():
            if node.get("type") == "module":
                node_clean = node_id.replace("\\", "/").replace(".py", "").replace("/", ".").strip(".")
                if q_clean == node_clean or node_id.endswith(query) or node.get("name") == query or node.get("path") == query:
                    return node_id
        return None

    def get_stats(self) -> Dict[str, int]:
        """
        Returns statistics of the indexed knowledge graph.
        """
        counts = {"module": 0, "class": 0, "function": 0}
        for node in self.nodes.values():
            ntype = node.get("type", "module")
            if ntype in counts:
                counts[ntype] += 1
            else:
                counts["module"] += 1

        return {
            "modules": counts["module"],
            "classes": counts["class"],
            "functions": counts["function"],
            "edges": len(self.edges)
        }
