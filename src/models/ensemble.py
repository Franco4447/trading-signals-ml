"""
Hybrid Multi-Model Ensemble Module.
Blends predictions from LightGBM, XGBoost, and CatBoost classifiers.
Calculates dynamic weighted ensemble probabilities:
P_ensemble = w_lgb * P_lgb + w_xgb * P_xgb + w_cat * P_cat
"""
from typing import Dict, Tuple, Optional
import numpy as np
import lightgbm as lgb
import xgboost as xgb

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

from src.utils.logger import setup_logger

logger = setup_logger("hybrid_ensemble")


class HybridEnsembleClassifier:
    """
    Ensemble Classifier combining LightGBM, XGBoost, and CatBoost.
    """
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {"lgb": 0.4, "xgb": 0.3, "cat": 0.3}
        
        self.lgb_model = lgb.LGBMClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            random_state=42,
            verbose=-1
        )
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            random_state=42,
            eval_metric="logloss"
        )
        if CATBOOST_AVAILABLE:
            self.cat_model = cb.CatBoostClassifier(
                iterations=100,
                learning_rate=0.05,
                depth=5,
                random_seed=42,
                verbose=0
            )
        else:
            self.cat_model = None

    def fit(self, X: np.ndarray, y: np.ndarray, sample_weights: Optional[np.ndarray] = None, sample_weight: Optional[np.ndarray] = None):
        """
        Fits all 3 models on the feature matrix.
        Maps labels {-1, 0, 1} to non-negative range for XGBoost {0, 1, 2}.
        """
        weights_to_use = sample_weights if sample_weights is not None else sample_weight
        valid_mask = y != 0
        X_clean = X[valid_mask]
        y_clean = y[valid_mask]
        w_clean = weights_to_use[valid_mask] if weights_to_use is not None else None

        if len(X_clean) < 10:
            logger.warning("Insufficient non-zero training samples (len(X_clean) < 10). Skipping ensemble fit.")
            return

        # Shift labels from {-1, 1} to {0, 1}
        y_mapped = np.where(y_clean == 1, 1, 0)

        self.lgb_model.fit(X_clean, y_mapped, sample_weight=w_clean)
        self.xgb_model.fit(X_clean, y_mapped, sample_weight=w_clean)
        
        if self.cat_model is not None:
            self.cat_model.fit(X_clean, y_mapped, sample_weight=w_clean)

        logger.info("Hybrid Ensemble (LightGBM + XGBoost + CatBoost) trained successfully.")

    def fit_dynamic_weights(
        self,
        X_val: np.ndarray,
        y_val: np.ndarray
    ):
        """
        Dynamically adjusts model weights proportional to Out-of-Sample (OOS) accuracy performance.
        Formula: w_m = Accuracy_m / sum(Accuracy_k)
        """
        valid_mask = y_val != 0
        if np.sum(valid_mask) < 5:
            return

        X_clean = X_val[valid_mask]
        y_mapped = np.where(y_val[valid_mask] == 1, 1, 0)

        acc_lgb = np.mean(self.lgb_model.predict(X_clean) == y_mapped)
        acc_xgb = np.mean(self.xgb_model.predict(X_clean) == y_mapped)
        
        if self.cat_model is not None:
            acc_cat = np.mean(self.cat_model.predict(X_clean) == y_mapped)
            total = acc_lgb + acc_xgb + acc_cat + 1e-8
            self.weights["lgb"] = round(float(acc_lgb / total), 4)
            self.weights["xgb"] = round(float(acc_xgb / total), 4)
            self.weights["cat"] = round(float(acc_cat / total), 4)
        else:
            total = acc_lgb + acc_xgb + 1e-8
            self.weights["lgb"] = round(float(acc_lgb / total), 4)
            self.weights["xgb"] = round(float(acc_xgb / total), 4)
            self.weights["cat"] = 0.0

        logger.info(f"Dynamic Ensemble Weights adjusted based on OOS accuracy: {self.weights}")


    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Returns blended class probabilities P(Buy) and P(Sell).
        """
        p_lgb = self.lgb_model.predict_proba(X)
        p_xgb = self.xgb_model.predict_proba(X)

        if self.cat_model is not None:
            p_cat = self.cat_model.predict_proba(X)
            p_ensemble = (
                self.weights["lgb"] * p_lgb +
                self.weights["xgb"] * p_xgb +
                self.weights["cat"] * p_cat
            )
        else:
            # Fallback to LGB + XGB if CatBoost not installed
            w_sum = self.weights["lgb"] + self.weights["xgb"]
            p_ensemble = (self.weights["lgb"] * p_lgb + self.weights["xgb"] * p_xgb) / w_sum

        return p_ensemble

    def predict_side(self, X: np.ndarray) -> np.ndarray:
        """
        Returns predicted side in {-1, +1}.
        """
        probs = self.predict_proba(X)
        p_buy = probs[:, 1]
        p_sell = probs[:, 0]
        
        sides = np.where(p_buy >= p_sell, 1, -1)
        return sides

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Standard sklearn/lgbm compatible predict method returning predicted side {-1, +1}.
        """
        return self.predict_side(X)

