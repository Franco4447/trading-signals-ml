"""
Signal Scaler & Bet Sizing Module.
Converts model predictions and meta-labeling probabilities into a continuous signal bounded in [-1.0, +1.0].
Applies Modified Kelly Bet Sizing scaling.
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
    """
    raw_signal = prob_buy - prob_sell
    clamped_signal = np.clip(raw_signal, min_bound, max_bound)
    return clamped_signal


def apply_macro_trend_filter(
    raw_signals: np.ndarray,
    macro_regimes_1d: np.ndarray
) -> np.ndarray:
    """
    Enforces the Strict Daily Macro Trend Filter (1d):
    - If 1d Macro Regime is Bearish (-1.0), Long signals (S_t > 0) are blocked (set to 0.0).
    - If 1d Macro Regime is Bullish (+1.0), Short signals (S_t < 0) are blocked (set to 0.0).
    """
    filtered_signals = raw_signals.copy()
    
    # Block Longs when Macro Regime is Bearish
    bearish_mask = macro_regimes_1d < 0
    filtered_signals[bearish_mask & (raw_signals > 0)] = 0.0
    
    # Block Shorts when Macro Regime is Bullish
    bullish_mask = macro_regimes_1d > 0
    filtered_signals[bullish_mask & (raw_signals < 0)] = 0.0
    
    return filtered_signals


def scale_meta_signal(
    primary_side: np.ndarray,
    meta_confidence: np.ndarray,
    min_confidence_threshold: float = 0.55,
    macro_regime_1d: np.ndarray | None = None
) -> np.ndarray:
    """
    Scales combined side predictions {-1, +1} and Meta-Model confidence P(meta) in [0, 1]
    into a continuous signal in range [-1.0, +1.0].
    Enforces the Strict Daily Macro Trend Filter (1d) if macro_regime_1d is supplied.
    """
    scaled_signal = np.zeros_like(primary_side, dtype=float)
    
    mask = meta_confidence >= min_confidence_threshold
    normalized_conf = (meta_confidence - min_confidence_threshold) / (1.0 - min_confidence_threshold + 1e-8)
    normalized_conf = np.clip(normalized_conf, 0.0, 1.0)
    
    scaled_signal[mask] = primary_side[mask] * normalized_conf[mask]
    scaled_signal = np.clip(scaled_signal, -1.0, 1.0)

    if macro_regime_1d is not None:
        scaled_signal = apply_macro_trend_filter(scaled_signal, macro_regime_1d)

    return scaled_signal


def calculate_fractional_kelly_bet_size(
    win_probability: float,
    win_loss_ratio: float = 1.5,
    fraction: float = 0.5
) -> float:
    """
    Calculates Fractional Kelly Criterion Bet Size.
    Formula: f* = (p * b - (1 - p)) / b
    Scaled by fractional multiplier (e.g. Half-Kelly 0.50) for capital preservation.
    """
    p = float(np.clip(win_probability, 0.0, 1.0))
    b = max(win_loss_ratio, 0.1)
    q = 1.0 - p

    full_kelly = (p * b - q) / b
    if full_kelly <= 0:
        return 0.0

    fractional_kelly = full_kelly * fraction
    return float(np.clip(fractional_kelly, 0.0, 1.0))


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


