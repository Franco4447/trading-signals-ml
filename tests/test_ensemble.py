"""
Unit tests for Hybrid Multi-Model Ensemble (LightGBM + XGBoost + CatBoost).
"""
import numpy as np
from src.models.ensemble import HybridEnsembleClassifier


def test_hybrid_ensemble_fit_predict():
    X = np.random.randn(100, 6)
    y = np.random.choice([-1, 1], size=100)
    w = np.ones(100)

    ensemble = HybridEnsembleClassifier()
    ensemble.fit(X, y, sample_weights=w)

    probs = ensemble.predict_proba(X)
    sides = ensemble.predict_side(X)

    assert probs.shape == (100, 2)
    assert len(sides) == 100
    assert set(sides).issubset({-1, 1})
    assert np.all((probs >= 0.0) & (probs <= 1.0))
