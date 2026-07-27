"""
AST Parser and repository scanner for Graphify.
Extracts module structure, classes, functions, docstrings, and import relationships
without importing or running arbitrary code.
"""
import ast
import os
from pathlib import Path
from typing import Optional, Set

from graphify.graph import KnowledgeGraph


IGNORED_DIRS: Set[str] = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache",
    ".agents", "build", "dist", ".graphify", "node_modules", ".gemini"
}


class ASTExtractor(ast.NodeVisitor):
    """
    AST Visitor that extracts structural metadata and dependencies from a single Python file.
    """
    def __init__(self, rel_path: str, module_name: str, graph: KnowledgeGraph):
        self.rel_path = rel_path
        self.module_name = module_name
        self.graph = graph
        self.current_class: Optional[str] = None

    def visit_Module(self, node: ast.Module) -> None:
        docstring = ast.get_docstring(node) or ""
        self.graph.add_node(
            node_id=self.rel_path,
            node_type="module",
            name=self.module_name,
            path=self.rel_path,
            docstring=docstring,
            lines=len(getattr(node, "body", []))
        )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        docstring = ast.get_docstring(node) or ""
        class_id = f"{self.rel_path}::{node.name}"
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)

        self.graph.add_node(
            node_id=class_id,
            node_type="class",
            name=node.name,
            path=self.rel_path,
            docstring=docstring,
            bases=bases,
            lineno=getattr(node, "lineno", 0)
        )
        self.graph.add_edge(self.rel_path, class_id, relation="defines")

        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node)

    def _process_function(self, node: ast.AST) -> None:
        name = getattr(node, "name", "unknown")
        docstring = ast.get_docstring(node) or ""
        lineno = getattr(node, "lineno", 0)

        args = []
        if hasattr(node, "args"):
            for arg in node.args.args:
                args.append(arg.arg)

        if self.current_class:
            func_id = f"{self.rel_path}::{self.current_class}.{name}"
            parent_id = f"{self.rel_path}::{self.current_class}"
            func_name = f"{self.current_class}.{name}"
        else:
            func_id = f"{self.rel_path}::{name}"
            parent_id = self.rel_path
            func_name = name

        self.graph.add_node(
            node_id=func_id,
            node_type="function",
            name=func_name,
            path=self.rel_path,
            docstring=docstring,
            args=args,
            lineno=lineno
        )
        self.graph.add_edge(parent_id, func_id, relation="defines")
        # Do not recurse into inner function definitions for clarity
        for child in ast.iter_child_nodes(node):
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.visit(child)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            target_mod = alias.name
            target_path = _module_to_rel_path(target_mod)
            self.graph.add_edge(self.rel_path, target_path, relation="imports")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            target_mod = node.module
            target_path = _module_to_rel_path(target_mod)
            self.graph.add_edge(self.rel_path, target_path, relation="imports")
            # Also check if importing a submodule
            for alias in node.names:
                sub_mod = f"{node.module}.{alias.name}"
                sub_path = _module_to_rel_path(sub_mod)
                self.graph.add_edge(self.rel_path, sub_path, relation="imports")


def _module_to_rel_path(module_name: str) -> str:
    """
    Converts a Python module dot-notation name to a relative file path in the repository.
    Example: 'src.features.technical_indicators' -> 'src/features/technical_indicators.py'
    """
    parts = module_name.split(".")
    return "/".join(parts) + ".py"


def extract_repository_graph(root_dir: str | Path) -> KnowledgeGraph:
    """
    Scans a Python repository directory, extracts AST metadata from all valid .py files,
    and returns a consolidated KnowledgeGraph.
    """
    root_path = Path(root_dir).resolve()
    graph = KnowledgeGraph()

    py_files = []
    for root, dirs, files in os.walk(root_path):
        # Filter out ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
        for file in files:
            if file.endswith(".py"):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(root_path).as_posix()
                py_files.append((full_path, rel_path))

    # First pass: Index all modules so we know valid targets
    valid_module_paths = set()
    for full_path, rel_path in py_files:
        valid_module_paths.add(rel_path)
        # Also map __init__.py package paths
        if rel_path.endswith("/__init__.py"):
            pkg_path = rel_path[:-12]
            valid_module_paths.add(pkg_path)

    # Second pass: Parse AST and build graph
    for full_path, rel_path in py_files:
        module_name = rel_path.replace(".py", "").replace("/", ".")
        if module_name.endswith(".__init__"):
            module_name = module_name[:-9]

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            tree = ast.parse(source_code, filename=str(full_path))
            extractor = ASTExtractor(rel_path=rel_path, module_name=module_name, graph=graph)
            extractor.visit(tree)
        except Exception as e:
            # Ignore syntax errors in broken or scratch scripts without crashing
            graph.add_node(
                node_id=rel_path,
                node_type="module",
                name=module_name,
                path=rel_path,
                docstring=f"AST Parse Error: {e}"
            )

    # Clean up import edges: only keep edges targeting valid modules within the repository
    clean_edges = []
    for edge in graph.edges:
        if edge["relation"] == "imports":
            tgt = edge["target"]
            # Try exact match or __init__.py match
            if tgt in valid_module_paths:
                clean_edges.append(edge)
            elif tgt.replace(".py", "/__init__.py") in valid_module_paths:
                edge_copy = dict(edge)
                edge_copy["target"] = tgt.replace(".py", "/__init__.py")
                clean_edges.append(edge_copy)
        else:
            clean_edges.append(edge)

    graph.edges = clean_edges
    # Rebuild index
    graph._out_edges.clear()
    graph._in_edges.clear()
    for edge in graph.edges:
        src, tgt = edge["source"], edge["target"]
        if src not in graph._out_edges:
            graph._out_edges[src] = []
        if tgt not in graph._in_edges:
            graph._in_edges[tgt] = []
        graph._out_edges[src].append(edge)
        graph._in_edges[tgt].append(edge)

    return graph
