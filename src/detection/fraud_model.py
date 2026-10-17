import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from src.utils.metrics import classification_metrics


MODEL_FEATURES = [
    "amount",
    "hour",
    "transactions_last_1h",
    "amount_last_1h",
    "account_age_days",
    "device_age_days",
    "is_new_device",
    "is_international",
    "failed_attempts",
    "merchant_risk",
    "ip_risk",
    "network_degree",
]


def train_fraud_model(
    df: pd.DataFrame,
    model_dir: str | Path,
):

    if "is_fraud" not in df.columns:
        raise ValueError(
            "Training data must contain is_fraud."
        )

    missing = [
        column
        for column in MODEL_FEATURES
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing model features: {missing}"
        )

    y = df["is_fraud"].astype(int)

    if y.nunique() < 2:
        raise ValueError(
            "Training data must contain both fraud and normal transactions."
        )

    model_dir = Path(model_dir)

    model_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    X = df[MODEL_FEATURES].copy()

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y,
        )
    )

    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=10,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train,
        y_train,
    )

    probabilities = (
        model.predict_proba(X_test)[:, 1]
    )

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    metrics = classification_metrics(
        y_test,
        predictions,
        probabilities,
    )

    joblib.dump(
        model,
        model_dir / "fraud_model.pkl",
    )

    (
        model_dir / "feature_columns.json"
    ).write_text(
        json.dumps(
            MODEL_FEATURES,
            indent=2,
        ),
        encoding="utf-8",
    )

    return model, metrics