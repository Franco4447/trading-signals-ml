#!/usr/bin/env bash
# Weekly MLOps Automated Retraining Cron Script
# Executed via crontab on VPS: 0 0 * * 0 /app/scripts/cron_retrain.sh

set -e

echo "[MLOps Cron] Starting Weekly Model Retraining..."
python -m src.pipeline.retrain --force-retrain
echo "[MLOps Cron] Retraining Completed Successfully at $(date)."
