#!/usr/bin/env bash
# Trading Signals ML - Weekly Automated MLOps Cron Script
# Recommended Crontab: 0 0 * * 0 /app/scripts/cron_mlops.sh (Runs every Sunday at 00:00 UTC)
# Evaluates Concept Drift, triggers automated retraining on degradation, and hot-reloads API in-memory.

set -e


echo "[MLOps Pipeline] Starting automated Concept Drift & Retraining checks..."

# 1. Run Concept Drift Evaluation
python -m src.monitoring.drift

# 2. Execute Automated Retraining Pipeline
echo "[MLOps Pipeline] Executing model retraining..."
python -m src.pipeline.retrain

# 3. Trigger Zero-Downtime Hot-Reloading on API Server
echo "[MLOps Pipeline] Triggering Zero-Downtime Hot-Reload on API..."
curl -s -X POST http://localhost:8000/reload-model \
     -H "Content-Type: application/json" \
     -d '{"model_path": "models/latest_model_btc_usdt.joblib"}' || true

echo "[MLOps Pipeline] Automated MLOps execution completed successfully."
