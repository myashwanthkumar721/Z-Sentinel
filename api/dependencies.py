from functools import lru_cache
from pathlib import Path

import joblib

from config.settings import settings
from src.detection.model_loader import (
    load_fraud_model,
)


@lru_cache
def get_fraud_model():

    return load_fraud_model(
        settings.model_dir
    )


@lru_cache
def get_anomaly_model():

    path = (
        Path(settings.model_dir)
        / "anomaly_model.pkl"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Anomaly model not found at {path}. "
            "Run scripts/train_anomaly_model.py first."
        )

    return joblib.load(path)