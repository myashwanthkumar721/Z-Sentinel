from pathlib import Path

import joblib


def load_fraud_model(
    model_dir: str | Path,
):

    path = (
        Path(model_dir)
        / "fraud_model.pkl"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Fraud model not found at {path}. "
            "Run scripts/train_model.py first."
        )

    return joblib.load(path)