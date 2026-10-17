from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest


ANOMALY_FEATURES = [
    "amount",
    "transactions_last_1h",
    "amount_last_1h",
    "account_age_days",
    "device_age_days",
    "failed_attempts",
    "merchant_risk",
    "ip_risk",
    "network_degree",
]


def train_anomaly_model(
    df: pd.DataFrame,
    model_dir: str | Path,
):

    missing = [
        column
        for column in ANOMALY_FEATURES
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing anomaly features: {missing}"
        )

    model_dir = Path(model_dir)

    model_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    model = IsolationForest(
        n_estimators=200,
        contamination=0.08,
        random_state=42,
    )

    X = (
        df[ANOMALY_FEATURES]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
        .fillna(0)
    )

    model.fit(X)

    joblib.dump(
        model,
        model_dir / "anomaly_model.pkl",
    )

    return model


def anomaly_score(
    model,
    transaction: dict,
) -> float:

    row = pd.DataFrame(
        [transaction]
    )

    for column in ANOMALY_FEATURES:
        if column not in row.columns:
            row[column] = 0.0

    X = (
        row[ANOMALY_FEATURES]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
        .fillna(0)
    )

    raw = float(
        model.decision_function(X)[0]
    )

    # IsolationForest normally produces
    # higher values for normal observations.
    score = 1.0 - (
        raw + 0.5
    )

    return max(
        0.0,
        min(
            1.0,
            score,
        ),
    )