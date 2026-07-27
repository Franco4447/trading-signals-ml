"""
Unit tests for Automated MLOps Retraining Pipeline.
"""
from src.pipeline.retrain import run_automated_retraining_pipeline


def test_automated_retraining_pipeline():
    res = run_automated_retraining_pipeline(
        ticker="BTC-USD",
        symbol="BTC/USDT",
        force_retrain=True
    )
    assert res["status"] in ["RETRAINED", "SKIPPED"]
    if res["status"] == "RETRAINED":
        assert "model_path" in res
        assert "version" in res
