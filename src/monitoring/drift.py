"""
Concept Drift Detection Module.
Monitors feature distribution shifts using Kolmogorov-Smirnov test to adjust leverage automatically.
"""

import numpy as np
import polars as pl
from scipy.stats import ks_2samp

from src.utils.logger import setup_logger

logger = setup_logger("concept_drift")


class ConceptDriftDetector:
    """
    Evaluates feature drift between baseline training set and live production window.
    """
    def __init__(self, p_value_threshold: float = 0.05):
        self.p_value_threshold = p_value_threshold
        self.baseline_features: dict[str, np.ndarray] = {}

    def fit_baseline(self, df_features: pl.DataFrame, feature_cols: list):
        """
        Stores baseline distributions from training dataset.
        """
        for col in feature_cols:
            if col in df_features.columns:
                vals = df_features[col].to_numpy()
                self.baseline_features[col] = vals[~np.isnan(vals)]
        logger.info(f"Concept Drift baseline stored for {len(self.baseline_features)} features.")

    def detect_drift(self, df_current: pl.DataFrame) -> dict:
        """
        Runs 2-sample Kolmogorov-Smirnov test on current window features.
        Returns drift status and suggested leverage multiplier reduction.
        """
        drift_results = {}
        drifted_count = 0

        for col, baseline in self.baseline_features.items():
            if col in df_current.columns:
                curr_vals = df_current[col].to_numpy()
                curr_clean = curr_vals[~np.isnan(curr_vals)]

                if len(curr_clean) < 10:
                    continue

                stat, p_val = ks_2samp(baseline, curr_clean)
                is_drifted = bool(p_val < self.p_value_threshold)
                if is_drifted:
                    drifted_count += 1

                drift_results[col] = {
                    "ks_stat": float(stat),
                    "p_value": float(p_val),
                    "is_drifted": is_drifted
                }

        drift_ratio = drifted_count / max(len(self.baseline_features), 1)
        
        # Risk Multiplier: Reduce leverage if >30% features show drift
        risk_multiplier = 1.0
        if drift_ratio >= 0.5:
            risk_multiplier = 0.25
        elif drift_ratio >= 0.3:
            risk_multiplier = 0.50

        logger.info(f"Concept Drift Check: {drifted_count}/{len(self.baseline_features)} features drifted. Risk Multiplier: {risk_multiplier}")

        return {
            "drift_ratio": float(drift_ratio),
            "risk_multiplier": float(risk_multiplier),
            "features_drift": drift_results
        }
