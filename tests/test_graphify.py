"""
Unit and integration tests for Graphify AST Indexer and Knowledge Graph engine.
"""
from pathlib import Path
import tempfile
from graphify.graph import KnowledgeGraph
from graphify.extractor import extract_repository_graph


def test_knowledge_graph_basic():
    graph = KnowledgeGraph()
    graph.add_node("src/mod_a.py", "module", "mod_a", "src/mod_a.py", "Module A doc")
    graph.add_node("src/mod_b.py", "module", "mod_b", "src/mod_b.py", "Module B doc")
    graph.add_edge("src/mod_a.py", "src/mod_b.py", "imports")

    assert "src/mod_a.py" in graph.nodes
    assert len(graph.edges) == 1

    deps = graph.get_dependencies("mod_a")
    assert "src/mod_b.py" in deps

    dependents = graph.get_dependents("mod_b")
    assert "src/mod_a.py" in dependents


def test_graph_query_search():
    graph = KnowledgeGraph()
    graph.add_node("1", "function", "calculate_sharpe", "src/metrics.py", "Computes Sharpe ratio")
    graph.add_node("2", "function", "fetch_data", "src/data.py", "Ingests crypto OHLCV")

    res = graph.query("sharpe")
    assert len(res) == 1
    assert res[0]["name"] == "calculate_sharpe"


def test_graph_persistence():
    graph = KnowledgeGraph()
    graph.add_node("x", "module", "mod_x", "src/mod_x.py", "Test persistence")

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_graph.json"
        graph.save(filepath)
        assert filepath.exists()

        loaded_graph = KnowledgeGraph.load(filepath)
        assert "x" in loaded_graph.nodes
        assert loaded_graph.nodes["x"]["docstring"] == "Test persistence"


def test_ast_extractor_repository():
    root_dir = Path(__file__).resolve().parent.parent
    graph = extract_repository_graph(root_dir)

    stats = graph.get_stats()
    assert stats["modules"] > 5
    assert stats["functions"] > 10

    # Test that logger or train module was indexed
    res = graph.query("setup_logger")
    assert len(res) >= 1
