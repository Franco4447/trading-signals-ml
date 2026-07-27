"""
Meta-Labeling Module (López de Prado Framework).
Combines Primary Model side prediction with Secondary Meta-Model confidence filtering.
"""

import lightgbm as lgb
import numpy as np

from src.utils.logger import setup_logger

logger = setup_logger("meta_labeling")


class MetaLabelingPipeline:
    """
    Two-stage architecture:
    1. Primary Model predicts market side m_t in {-1, +1} (Long/Short).
    2. Meta Model predicts probability P(meta = 1) that primary prediction succeeds.
    """
    def __init__(self, primary_model=None):
        from src.models.ensemble import HybridEnsembleClassifier
        self.primary_model = primary_model or HybridEnsembleClassifier()
        self.meta_model = lgb.LGBMClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4,
            random_state=42,
            verbose=-1
        )
        
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weights: np.ndarray = None
    ):
        """
        Fits Primary Model on triple barrier labels {-1, 0, +1} and Meta-Model on binary success labels {0, 1}.
        """
        # Primary Model fits non-zero labels
        valid_mask = y != 0
        X_pri = X[valid_mask]
        y_pri = y[valid_mask]
        w_pri = sample_weights[valid_mask] if sample_weights is not None else None

        self.primary_model.fit(X_pri, y_pri, sample_weight=w_pri)
        
        # Primary Predictions
        primary_preds = self.primary_model.predict(X)
        
        # Meta Labels: 1 if Primary side matches true label, 0 otherwise
        y_meta = np.where(primary_preds == y, 1, 0)
        
        # Fit Meta-Model on all features to predict meta probability
        self.meta_model.fit(X, y_meta, sample_weight=sample_weights)
        logger.info("Meta-Labeling pipeline successfully trained.")

    def predict_confidence(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns:
            primary_side: Predicted side in {-1, +1}
            meta_prob: Confidence probability in [0.0, 1.0] that trade succeeds
        """
        primary_side = self.primary_model.predict(X)
        meta_probs = self.meta_model.predict_proba(X)[:, 1]
        return primary_side, meta_probs
