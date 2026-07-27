"""
Pipeline Package.
Includes automated MLOps retraining.
"""
from src.pipeline.retrain import run_automated_retraining_pipeline

__all__ = ["run_automated_retraining_pipeline"]
