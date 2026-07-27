"""
Features package.
"""
from src.features.technical_indicators import (
    add_advanced_features,
    find_optimal_d,
    fractional_differentiation,
    get_fracdiff_weights,
)

# Alias for backwards compatibility
add_technical_features = add_advanced_features

__all__ = [
    "add_advanced_features",
    "add_technical_features",
    "fractional_differentiation",
    "get_fracdiff_weights",
    "find_optimal_d"
]
