"""
Z-Sentinel - PaySim Threshold Analysis

------------
Evaluates the PaySim fraud model across multiple probability
thresholds.

This is an analysis-only script.
It does NOT modify or replace any existing model.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
)


# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "paysim_features.csv"
)

MODEL_FILE = (
    BASE_DIR
    / "models"
    / "paysim_fraud_model.pkl"
)

FEATURE_FILE = (
    BASE_DIR
    / "models"
    / "paysim_feature_columns.json"
)


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

CHUNK_SIZE = 250_000

TRAIN_RATIO = 0.80

THRESHOLDS = [
    0.01,
    0.02,
    0.05,
    0.10,
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
    0.95,
]


# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------

def validate_files() -> None:
    """Verify required model and dataset files exist."""

    required_files = [
        DATA_FILE,
        MODEL_FILE,
        FEATURE_FILE,
    ]

    for file_path in required_files:

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found:\n{file_path}"
            )


# -------------------------------------------------------------------
# Load model
# -------------------------------------------------------------------

def load_model():

    print()
    print("=" * 70)
    print("LOADING PAYSim FRAUD MODEL")
    print("=" * 70)

    model = joblib.load(
        MODEL_FILE
    )

    print(
        f"Model loaded from:\n{MODEL_FILE}"
    )

    return model


# -------------------------------------------------------------------
# Load feature columns
# -------------------------------------------------------------------

def load_feature_columns() -> list[str]:

    import json

    with open(
        FEATURE_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        features = json.load(file)

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            "Feature column file must contain a list."
        )

    print()
    print(
        f"Model features: {len(features)}"
    )

    return features


# -------------------------------------------------------------------
# Determine test rows
# -------------------------------------------------------------------

def count_rows() -> int:

    total_rows = 0

    for chunk in pd.read_csv(
        DATA_FILE,
        usecols=["is_fraud"],
        chunksize=CHUNK_SIZE,
    ):
        total_rows += len(chunk)

    return total_rows


# -------------------------------------------------------------------
# Generate test predictions
# -------------------------------------------------------------------

def generate_test_predictions(
    model,
    features: list[str],
) -> tuple[np.ndarray, np.ndarray]:

    print()
    print("=" * 70)
    print("GENERATING TEST-SET PREDICTIONS")
    print("=" * 70)

    total_rows = count_rows()

    train_rows = int(
        total_rows * TRAIN_RATIO
    )

    print(
        f"Total rows : {total_rows:,}"
    )

    print(
        f"Train rows : {train_rows:,}"
    )

    print(
        f"Test rows  : "
        f"{total_rows - train_rows:,}"
    )

    usecols = (
        features
        + ["is_fraud"]
    )

    probabilities = []
    labels = []

    rows_seen = 0

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            DATA_FILE,
            usecols=usecols,
            chunksize=CHUNK_SIZE,
        ),
        start=1,
    ):

        chunk_start = rows_seen

        chunk_end = (
            rows_seen
            + len(chunk)
        )

        rows_seen = chunk_end

        # Entire chunk belongs to training section.
        if chunk_end <= train_rows:
            continue

        # Chunk crosses train/test boundary.
        if chunk_start < train_rows:

            offset = (
                train_rows
                - chunk_start
            )

            chunk = chunk.iloc[
                offset:
            ].copy()

        if chunk.empty:
            continue

        X = chunk[
            features
        ]

        y = chunk[
            "is_fraud"
        ]

        chunk_probabilities = (
            model.predict_proba(X)[:, 1]
        )

        probabilities.append(
            chunk_probabilities
        )

        labels.append(
            y.to_numpy()
        )

        print(
            f"Chunk {chunk_number:02d} | "
            f"processed={len(chunk):,}"
        )

    if not probabilities:
        raise RuntimeError(
            "No test predictions were generated."
        )

    y_probability = np.concatenate(
        probabilities
    )

    y_true = np.concatenate(
        labels
    )

    print()
    print(
        f"Test predictions: "
        f"{len(y_true):,}"
    )

    print(
        f"Test fraud cases: "
        f"{int(y_true.sum()):,}"
    )

    return y_true, y_probability


# -------------------------------------------------------------------
# Threshold analysis
# -------------------------------------------------------------------

def analyze_thresholds(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> pd.DataFrame:

    print()
    print("=" * 70)
    print("THRESHOLD ANALYSIS")
    print("=" * 70)

    rows = []

    for threshold in THRESHOLDS:

        predictions = (
            probabilities >= threshold
        ).astype(int)

        precision = precision_score(
            y_true,
            predictions,
            zero_division=0,
        )

        recall = recall_score(
            y_true,
            predictions,
            zero_division=0,
        )

        f1 = f1_score(
            y_true,
            predictions,
            zero_division=0,
        )

        tp = int(
            (
                (y_true == 1)
                & (predictions == 1)
            ).sum()
        )

        fp = int(
            (
                (y_true == 0)
                & (predictions == 1)
            ).sum()
        )

        fn = int(
            (
                (y_true == 1)
                & (predictions == 0)
            ).sum()
        )

        tn = int(
            (
                (y_true == 0)
                & (predictions == 0)
            ).sum()
        )

        alerts = int(
            predictions.sum()
        )

        rows.append(
            {
                "threshold": threshold,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "alerts": alerts,
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "true_negatives": tn,
            }
        )

    results = pd.DataFrame(
        rows
    )

    print()

    print(
        f"{'Threshold':>10} "
        f"{'Precision':>10} "
        f"{'Recall':>10} "
        f"{'F1':>10} "
        f"{'Alerts':>10} "
        f"{'FP':>10} "
        f"{'FN':>10}"
    )

    print("-" * 80)

    for _, row in results.iterrows():

        print(
            f"{row['threshold']:>10.2f} "
            f"{row['precision']:>10.4f} "
            f"{row['recall']:>10.4f} "
            f"{row['f1']:>10.4f} "
            f"{int(row['alerts']):>10,} "
            f"{int(row['false_positives']):>10,} "
            f"{int(row['false_negatives']):>10,}"
        )

    return results


# -------------------------------------------------------------------
# PR-AUC
# -------------------------------------------------------------------

def show_pr_auc(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> None:

    pr_auc = average_precision_score(
        y_true,
        probabilities,
    )

    print()
    print(
        f"Overall PR-AUC: {pr_auc:.4f}"
    )


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main() -> None:

    print("=" * 70)
    print("Z-SENTINEL - PAYSIM THRESHOLD ANALYSIS")
    print("=" * 70)

    validate_files()

    model = load_model()

    features = load_feature_columns()

    y_true, probabilities = (
        generate_test_predictions(
            model,
            features,
        )
    )

    results = analyze_thresholds(
        y_true,
        probabilities,
    )

    show_pr_auc(
        y_true,
        probabilities,
    )

    print()
    print("=" * 70)
    print("THRESHOLD ANALYSIS COMPLETE")
    print("=" * 70)

    print()
    print(
        "No model files were modified."
    )


if __name__ == "__main__":
    main()