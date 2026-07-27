"""
Bayesian Hyperparameter Optimization Module using Optuna (Per-Asset Tuning).
Optimizes Sortino Ratio Out-of-Sample while constraining Max Drawdown < 15%.
"""

import numpy as np
import optuna
import polars as pl

from src.backtest.engine import run_leverage_backtest
from src.features.technical_indicators import add_advanced_features
from src.models.train import train_model_pipeline
from src.utils.logger import setup_logger

logger = setup_logger("optuna_tuning")
optuna.logging.set_verbosity(optuna.logging.WARNING)


def optimize_asset_parameters(
    df_raw: pl.DataFrame,
    symbol: str = "BTC/USDT",
    n_trials: int = 20
) -> dict:
    """
    Executes Optuna study to find optimal asset parameters for (pt_multiplier, sl_multiplier, FracDiff d*).
    
    Parameters:
        df_raw: Raw OHLCV DataFrame for the asset.
        symbol: Trading pair name.
        n_trials: Number of Bayesian search iterations.
        
    Returns:
        Best parameter dictionary and objective value.
    """
    logger.info(f"Starting Optuna Bayesian Hyperparameter Optimization for {symbol} ({n_trials} trials)...")

    def objective(trial: optuna.Trial) -> float:
        pt_mult = trial.suggest_float("pt_multiplier", 1.0, 3.0, step=0.2)
        sl_mult = trial.suggest_float("sl_multiplier", 0.5, 2.0, step=0.1)
        d_val = trial.suggest_float("optimal_d", 0.20, 0.50, step=0.05)

        # 1. Feature Engineering with candidate FracDiff d*
        df_feat = add_advanced_features(df_raw, optimal_d=d_val)

        # 2. Model Pipeline Training
        pipeline_res = train_model_pipeline(df_feat)
        logger.debug(f"Trial candidate params: pt={pt_mult}, sl={sl_mult}, d={d_val}")
        pipeline = pipeline_res["pipeline"]
        feature_cols = pipeline_res["feature_cols"]
        df_labeled = pipeline_res["labeled_df"]

        # 3. Out-of-sample predictions
        X = df_labeled.select(feature_cols).to_numpy()
        sides, confs = pipeline.predict_confidence(X)
        
        # Continuous signal
        signals = np.where(confs >= 0.55, sides * confs, 0.0)
        df_backtest = df_labeled.with_columns([
            pl.Series("signal", signals)
        ])

        # 4. Backtest evaluation
        bt_res = run_leverage_backtest(
            df_backtest,
            leverage=3.0,
            signal_threshold=0.3
        )

        sortino = bt_res["sortino_ratio"]
        mdd = bt_res["max_drawdown"]

        # Penalty if Max Drawdown exceeds 15%
        if mdd > 0.15:
            sortino -= (mdd - 0.15) * 10.0

        return sortino

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    best_params = study.best_params
    best_value = study.best_value
    logger.info(f"Optuna Optimization for {symbol} Complete. Best Sortino: {best_value:.4f}, Best Params: {best_params}")

    return {
        "symbol": symbol,
        "best_params": best_params,
        "best_sortino": float(best_value)
    }
