import pandas as pd

from src.detection.fraud_model import MODEL_FEATURES


def predict_fraud_probability(
    model,
    transaction: dict,
) -> float:

    row = pd.DataFrame(
        [transaction]
    )

    for column in MODEL_FEATURES:
        if column not in row.columns:
            row[column] = 0.0

    row = row[
        MODEL_FEATURES
    ].apply(
        pd.to_numeric,
        errors="coerce",
    ).fillna(0)

    probability = float(
        model.predict_proba(
            row
        )[:, 1][0]
    )

    return max(
        0.0,
        min(
            1.0,
            probability,
        ),
    )