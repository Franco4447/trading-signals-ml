"""
Model Training & Purged Walk-Forward Cross-Validation Module.
Guarantees anti-leakage with Embargo and Sample Uniqueness weighting.
"""

import os
import yaml
import numpy as np
import polars as pl

from src.models.meta_labeling import MetaLabelingPipeline
from src.models.triple_barrier import (
    apply_triple_barrier_labeling,
    compute_sample_uniqueness_weights,
)
from src.utils.logger import setup_logger

logger = setup_logger("train_pipeline")


def load_config(config_path: str = "config/default_config.yaml") -> dict:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def purged_walk_forward_splits(
    n_samples: int,
    n_splits: int = 5,
    embargo_pct: float = 0.05
) -> list[tuple[np.ndarray, np.ndarray]]:
    """
    Generates Purged Walk-Forward temporal splits with Embargo to eliminate data leakage.
    """
    splits = []
    fold_size = n_samples // (n_splits + 1)
    embargo_size = int(n_samples * embargo_pct)

    for i in range(n_splits):
        train_end = (i + 1) * fold_size
        test_start = train_end + embargo_size
        test_end = test_start + fold_size

        if test_end > n_samples:
            break

        train_indices = np.arange(0, train_end)
        test_indices = np.arange(test_start, test_end)
        splits.append((train_indices, test_indices))

    logger.info(f"Generated {len(splits)} Purged Walk-Forward splits with {embargo_pct*100}% embargo.")
    return splits


def train_model_pipeline(df_features: pl.DataFrame, n_splits: int | None = None) -> dict:
    """
    Executes complete ML training pipeline:
    1. Triple Barrier Labeling
    2. Sample Uniqueness Weights computation (normalized strictly per fold)
    3. Purged Walk-Forward CV with Dynamic OOS Ensemble Weighting
    4. Meta-Labeling training
    """
    if n_splits is None:
        cfg = load_config()
        n_splits = cfg.get("training", {}).get("n_splits", 5)

    df_labeled = apply_triple_barrier_labeling(df_features)
    weights = compute_sample_uniqueness_weights(df_labeled)

    feature_cols = [c for c in df_labeled.columns if c.startswith("feature_")]
    X = df_labeled.select(feature_cols).to_numpy()
    y = df_labeled["label"].to_numpy()

    splits = purged_walk_forward_splits(len(df_labeled), n_splits=n_splits)
    
    cv_scores = []
    pipeline = MetaLabelingPipeline()

    for fold, (train_idx, test_idx) in enumerate(splits):
        X_train, y_train = X[train_idx], y[train_idx]
        w_train = weights[train_idx]
        # Normalize weights strictly within fold to prevent leakage
        w_train_norm = w_train / (np.mean(w_train) + 1e-8)
        
        X_test, y_test = X[test_idx], y[test_idx]

        pipeline.fit(X_train, y_train, sample_weights=w_train_norm)
        
        # Dynamically adjust OOS ensemble weights on validation fold
        if hasattr(pipeline.primary_model, "fit_dynamic_weights"):
            pipeline.primary_model.fit_dynamic_weights(X_test, y_test)

        sides, confs = pipeline.predict_confidence(X_test)
        
        # Accuracy of non-zero predictions
        valid_mask = y_test != 0
        if np.sum(valid_mask) > 0:
            acc = np.mean(sides[valid_mask] == y_test[valid_mask])
            cv_scores.append(acc)
            logger.info(f"Fold {fold+1} Accuracy: {acc:.4f}")

    # Final fit on full dataset
    w_norm = weights / (np.mean(weights) + 1e-8)
    pipeline.fit(X, y, sample_weights=w_norm)
    logger.info(f"Full training pipeline completed. Mean Out-of-Sample CV Accuracy: {np.mean(cv_scores):.4f}")

    return {
        "pipeline": pipeline,
        "feature_cols": feature_cols,
        "mean_cv_accuracy": float(np.mean(cv_scores)) if cv_scores else 0.0,
        "labeled_df": df_labeled
    }
