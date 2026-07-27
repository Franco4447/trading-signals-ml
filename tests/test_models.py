"""
Unit tests for Triple Barrier Labeling, Meta-Labeling, and Purged CV.
"""
import numpy as np
import polars as pl

from src.models.meta_labeling import MetaLabelingPipeline
from src.models.train import purged_walk_forward_splits
from src.models.triple_barrier import (
    apply_triple_barrier_labeling,
)


def test_triple_barrier_labeling():
    df = pl.DataFrame({
        "close": np.array([100.0, 105.0, 110.0, 95.0, 90.0, 100.0, 102.0, 101.0, 103.0, 105.0]),
        "feature_volatility_20": np.ones(10) * 2.0
    })

    df_labeled = apply_triple_barrier_labeling(df, pt_multiplier=1.5, sl_multiplier=1.0, vertical_barrier_lags=3)
    assert "label" in df_labeled.columns
    unique_labels = set(df_labeled["label"].unique().to_list())
    assert unique_labels.issubset({-1, 0, 1})


def test_purged_walk_forward_splits():
    splits = purged_walk_forward_splits(n_samples=100, n_splits=3, embargo_pct=0.05)
    assert len(splits) > 0
    for train_idx, test_idx in splits:
        assert len(train_idx) > 0
        assert len(test_idx) > 0
        # Assert embargo gap exists between train_end and test_start
        assert test_idx[0] > train_idx[-1]


def test_meta_labeling_pipeline():
    X = np.random.randn(100, 5)
    y = np.random.choice([-1, 0, 1], size=100)
    w = np.ones(100)

    pipeline = MetaLabelingPipeline()
    pipeline.fit(X, y, sample_weights=w)
    sides, confs = pipeline.predict_confidence(X)

    assert len(sides) == 100
    assert len(confs) == 100
    assert np.all((confs >= 0.0) & (confs <= 1.0))
