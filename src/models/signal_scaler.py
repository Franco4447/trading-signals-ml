"""
Signal Scaler Module.
Converts probabilities or model outputs into a continuous signal bounded in [-1.0, +1.0].
"""
import numpy as np


def scale_probabilities_to_signal(
    prob_sell: np.ndarray,
    prob_buy: np.ndarray,
    min_bound: float = -1.0,
    max_bound: float = 1.0
) -> np.ndarray:
    """
    Scales class probabilities into a continuous signal in range [-1.0, +1.0].
    
    Formula: Signal = prob_buy - prob_sell
    
    Parameters:
        prob_sell: Array of probabilities for sell class (-1)
        prob_buy: Array of probabilities for buy class (+1)
        min_bound: Minimum output clamp value (default -1.0)
        max_bound: Maximum output clamp value (default 1.0)
        
    Returns:
        np.ndarray of continuous signals bounded strictly in [min_bound, max_bound]
    """
    raw_signal = prob_buy - prob_sell
    clamped_signal = np.clip(raw_signal, min_bound, max_bound)
    return clamped_signal

def scale_regression_return_to_signal(
    predicted_returns: np.ndarray,
    volatility: np.ndarray,
    factor: float = 1.5
) -> np.ndarray:
    """
    Scales predicted continuous returns into a signal in [-1.0, +1.0] using hyperbolic tangent.
    
    Formula: Signal = tanh( predicted_returns / (factor * volatility) )
    """
    safe_volatility = np.where(volatility <= 0, 1e-6, volatility)
    normalized_returns = predicted_returns / (factor * safe_volatility)
    signal = np.tanh(normalized_returns)
    return np.clip(signal, -1.0, 1.0)
