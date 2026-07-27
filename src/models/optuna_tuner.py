"""
Optuna Hyperparameter Optimization Module.
Performs Bayesian optimization targeting Out-of-Sample Sharpe Ratio
over Purged Walk-Forward Cross-Validation splits.
"""
import optuna
import numpy as np
import polars as pl
import lightgbm as lgb
import xgboost as xgb

try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    CatBoostClassifier = None


from src.models.triple_barrier import apply_triple_barrier_labeling, compute_sample_uniqueness_weights
from src.models.train import purged_walk_forward_splits
from src.backtest.metrics import calculate_sharpe_ratio
from src.utils.logger import setup_logger


logger = setup_logger("optuna_tuner")

# Suppress Optuna verbose logging
optuna.logging.set_verbosity(optuna.logging.WARNING)


def objective_sharpe_ratio(
    trial: optuna.Trial,
    X: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray,
    splits: list[tuple[np.ndarray, np.ndarray]],
    model_type: str = "lightgbm"
) -> float:
    """
    Optuna objective function maximizing Out-of-Sample Sharpe Ratio over Purged CV splits.
    """
    sharpe_scores = []
    
    for train_idx, test_idx in splits:
        X_train, y_train = X[train_idx], y[train_idx]
        w_train = weights[train_idx]
        X_test, y_test = X[test_idx], y[test_idx]
        
        # Filter binary classification target (ignore expired 0 labels)
        mask_train = y_train != 0
        if np.sum(mask_train) < 10:
            continue
            
        X_train_b = X_train[mask_train]
        y_train_b = np.where(y_train[mask_train] == 1, 1, 0)
        w_train_b = w_train[mask_train]

        mask_test = y_test != 0
        if np.sum(mask_test) < 5:
            continue
        X_test_b = X_test[mask_test]
        y_test_b = np.where(y_test[mask_test] == 1, 1, 0)

        if model_type == "lightgbm":
            params = {
                "objective": "binary",
                "metric": "binary_logloss",
                "verbosity": -1,
                "n_estimators": trial.suggest_int("n_estimators", 20, 150),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                "max_depth": trial.suggest_int("max_depth", 3, 8),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True)
            }
            model = lgb.LGBMClassifier(**params)
            model.fit(X_train_b, y_train_b, sample_weight=w_train_b)
            probs = model.predict_proba(X_test_b)[:, 1]

        elif model_type == "xgboost":
            params = {
                "objective": "binary:logistic",
                "eval_metric": "logloss",
                "n_estimators": trial.suggest_int("n_estimators", 20, 150),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                "max_depth": trial.suggest_int("max_depth", 3, 8),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0)
            }
            model = xgb.XGBClassifier(**params)
            model.fit(X_train_b, y_train_b, sample_weight=w_train_b)
            probs = model.predict_proba(X_test_b)[:, 1]

        else:  # catboost with fallback
            if CATBOOST_AVAILABLE and CatBoostClassifier is not None:
                params = {
                    "iterations": trial.suggest_int("iterations", 20, 150),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
                    "depth": trial.suggest_int("depth", 3, 8),
                    "verbose": 0
                }
                model = CatBoostClassifier(**params)
                model.fit(X_train_b, y_train_b, sample_weight=w_train_b)
                probs = model.predict_proba(X_test_b)[:, 1]
            else:
                params = {
                    "objective": "binary",
                    "verbosity": -1,
                    "n_estimators": trial.suggest_int("n_estimators", 20, 150),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True)
                }
                model = lgb.LGBMClassifier(**params)
                model.fit(X_train_b, y_train_b, sample_weight=w_train_b)
                probs = model.predict_proba(X_test_b)[:, 1]


        # Calculate synthetic returns for Sharpe ratio
        returns = (probs - 0.5) * 2.0 * np.where(y_test_b == 1, 0.02, -0.02)
        sharpe = calculate_sharpe_ratio(returns)
        sharpe_scores.append(sharpe)


    return float(np.mean(sharpe_scores)) if sharpe_scores else 0.0


def tune_model_hyperparameters(
    df_features: pl.DataFrame,
    model_type: str = "lightgbm",
    n_trials: int = 15
) -> dict:
    """
    Executes Optuna Bayesian hyperparameter tuning targeting Out-of-Sample Sharpe Ratio.
    """
    logger.info(f"Starting Optuna hyperparameter optimization for {model_type} ({n_trials} trials)...")
    df_labeled = apply_triple_barrier_labeling(df_features)
    weights = compute_sample_uniqueness_weights(df_labeled)

    feature_cols = [c for c in df_labeled.columns if c.startswith("feature_")]
    X = df_labeled.select(feature_cols).to_numpy()
    y = df_labeled["label"].to_numpy()

    splits = purged_walk_forward_splits(len(df_labeled), n_splits=3)

    study = optuna.create_study(direction="maximize")
    study.optimize(
        lambda trial: objective_sharpe_ratio(trial, X, y, weights, splits, model_type=model_type),
        n_trials=n_trials
    )

    logger.info(f"Optuna Optimization complete for {model_type}. Best OOS Sharpe Ratio: {study.best_value:.4f}")
    logger.info(f"Best Hyperparameters: {study.best_params}")

    return {
        "best_params": study.best_params,
        "best_sharpe_ratio": float(study.best_value)
    }
