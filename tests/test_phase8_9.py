"""
Unit tests for Phase 8 (Optuna Tuner, Dynamic Hybrid Ensemble, Fractional Kelly Bet Sizing)
and Phase 9 (Dashboard REST API Endpoints).
"""
import numpy as np
import polars as pl
import pytest
from fastapi.testclient import TestClient


from src.api.server import app
from src.models.ensemble import HybridEnsembleClassifier
from src.models.optuna_tuner import tune_model_hyperparameters
from src.models.signal_scaler import calculate_fractional_kelly_bet_size

client = TestClient(app)


def test_fractional_kelly_bet_sizing():
    # High win prob (0.70) with 1.5 win/loss ratio -> Positive Kelly bet size
    size1 = calculate_fractional_kelly_bet_size(win_probability=0.70, win_loss_ratio=1.5, fraction=0.5)
    assert size1 > 0.0
    assert size1 <= 1.0

    # Low win prob (0.30) -> Negative Kelly clamped to 0.0
    size2 = calculate_fractional_kelly_bet_size(win_probability=0.30, win_loss_ratio=1.5, fraction=0.5)
    assert size2 == 0.0


def test_hybrid_ensemble_dynamic_weights():
    X = np.random.normal(size=(50, 10))
    y = np.random.choice([-1, 1], size=50)
    
    ensemble = HybridEnsembleClassifier()
    ensemble.fit(X, y)
    
    # Fit dynamic weights on validation set
    ensemble.fit_dynamic_weights(X, y)
    assert "lgb" in ensemble.weights
    assert "xgb" in ensemble.weights
    assert sum(ensemble.weights.values()) == pytest.approx(1.0, abs=1e-2)


def test_optuna_tuner_sharpe_optimization():
    dates = pl.datetime_range(start=pl.datetime(2024, 1, 1), end=pl.datetime(2024, 1, 10), interval="1h", eager=True)
    n = len(dates)
    prices = 40000.0 + np.cumsum(np.random.normal(size=n) * 100)
    
    df = pl.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": prices + 50,
        "low": prices - 50,
        "close": prices,
        "volume": np.full(n, 100.0),
        "feature_fracdiff": np.random.normal(size=n),
        "feature_volatility_20": np.full(n, 200.0),
        "feature_zscore_20": np.random.normal(size=n)
    })
    
    res = tune_model_hyperparameters(df, model_type="lightgbm", n_trials=3)
    assert "best_params" in res
    assert "best_sharpe_ratio" in res


def test_dashboard_api_endpoints():
    r1 = client.get("/metrics/performance")
    assert r1.status_code == 200
    assert "sharpe_ratio" in r1.json()

    r2 = client.get("/dashboard/stats")
    assert r2.status_code == 200
    assert "balance" in r2.json()

    r3 = client.get("/drift/status")
    assert r3.status_code == 200
    assert "drift_detected" in r3.json()
