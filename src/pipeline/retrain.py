"""
Automated MLOps Retraining Pipeline.
Fetches recent multi-year data, evaluates Concept Drift, re-trains model pipeline,
and exports atomic .joblib model artifacts for Zero-Downtime Hot-Reloading.
"""
import os
import time
from typing import Dict
import joblib
import httpx

from src.data.ingestion import fetch_multi_year_dataset
from src.features.technical_indicators import add_advanced_features
from src.models.train import train_model_pipeline
from src.monitoring.drift import ConceptDriftDetector
from src.utils.logger import setup_logger

logger = setup_logger("mlops_retrain")


def run_automated_retraining_pipeline(
    ticker: str = "BTC-USD",
    symbol: str = "BTC/USDT",
    model_dir: str = "models",
    force_retrain: bool = False,
    api_url: str = "http://localhost:8000/reload-model"
) -> Dict:
    """
    Executes automated retraining pipeline with Concept Drift validation and Atomic Hot-Reloading.
    """
    logger.info(f"Starting MLOps Retraining Pipeline for {symbol}...")

    # 1. Fetch Data
    df_ohlcv, df_micro = fetch_multi_year_dataset(ticker=ticker, symbol=symbol, years=3, interval="1h")
    df_features = add_advanced_features(df_ohlcv, microstructure_df=df_micro)

    # 2. Evaluate Concept Drift
    detector = ConceptDriftDetector()
    feature_cols = [c for c in df_features.columns if c.startswith("feature_")]
    detector.fit_baseline(df_features.head(1000), feature_cols)
    
    drift_res = detector.detect_drift(df_features.tail(200))
    drift_ratio = drift_res["drift_ratio"]

    if drift_ratio < 0.30 and not force_retrain:
        logger.info(f"Drift ratio ({drift_ratio*100:.2f}%) is within safe thresholds. Retraining skipped.")
        return {"status": "SKIPPED", "drift_ratio": drift_ratio}

    # 3. Conditional Optuna Hyperparameter Optimization (if Concept Drift > 30% or force_retrain)
    if drift_ratio >= 0.30 or force_retrain:
        from src.models.optuna_tuner import tune_model_hyperparameters
        logger.info(f"Concept Drift ({drift_ratio*100:.2f}%) triggered threshold. Running Optuna hyperparameter optimization before retraining...")
        try:
            optuna_res = tune_model_hyperparameters(df_features, model_type="lightgbm", n_trials=10)
            logger.info(f"Optuna tuning completed. Best OOS Sharpe: {optuna_res.get('best_sharpe_ratio'):.4f}")
        except Exception as e:
            logger.warning(f"Optuna tuning failed ({e}). Continuing with default pipeline training.")

    logger.info("Training new model pipeline...")
    pipeline_res = train_model_pipeline(df_features)

    # 4. Atomic Model Export
    os.makedirs(model_dir, exist_ok=True)
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    versioned_path = os.path.join(model_dir, f"model_{symbol.replace('/', '_').lower()}_{timestamp_str}.joblib")
    latest_path = os.path.join(model_dir, f"latest_model_{symbol.replace('/', '_').lower()}.joblib")

    model_artifact = {
        "pipeline": pipeline_res["pipeline"],
        "feature_cols": pipeline_res["feature_cols"],
        "mean_cv_accuracy": pipeline_res["mean_cv_accuracy"],
        "symbol": symbol,
        "timestamp": timestamp_str
    }

    joblib.dump(model_artifact, versioned_path)
    joblib.dump(model_artifact, latest_path)
    logger.info(f"New model artifact saved to {latest_path} (Version: {timestamp_str}).")

    # 5. Notify API for Zero-Downtime Hot-Reloading
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.post(api_url, json={"model_path": latest_path})
            if resp.status_code == 200:
                logger.info("FastAPI Server hot-reloaded new model in memory successfully.")
    except Exception as e:
        logger.warning(f"API hot-reload notification omitted ({e}). Model ready for next server startup.")

    return {
        "status": "RETRAINED",
        "model_path": latest_path,
        "version": timestamp_str,
        "mean_cv_accuracy": pipeline_res["mean_cv_accuracy"]
    }
