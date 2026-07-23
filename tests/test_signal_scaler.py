"""
Unit tests for the Signal Scaler module [-1.0, +1.0].
"""
import numpy as np
import pytest

from src.models.signal_scaler import (
    scale_probabilities_to_signal,
    scale_regression_return_to_signal,
)


def test_scale_probabilities_bounds():
    prob_sell = np.array([0.9, 0.1, 0.4, 0.0])
    prob_buy = np.array([0.0, 0.8, 0.4, 1.0])
    
    signals = scale_probabilities_to_signal(prob_sell, prob_buy)
    
    assert np.all(signals >= -1.0)
    assert np.all(signals <= 1.0)
    assert signals[0] == pytest.approx(-0.9)
    assert signals[1] == pytest.approx(0.7)
    assert signals[2] == pytest.approx(0.0)
    assert signals[3] == pytest.approx(1.0)

def test_scale_regression_return_bounds():
    predicted_returns = np.array([-0.5, -0.01, 0.0, 0.02, 0.8])
    volatility = np.array([0.02, 0.02, 0.02, 0.02, 0.02])
    
    signals = scale_regression_return_to_signal(predicted_returns, volatility)
    
    assert np.all(signals >= -1.0)
    assert np.all(signals <= 1.0)
    assert signals[0] < -0.99
    assert signals[2] == 0.0
    assert signals[4] > 0.99
