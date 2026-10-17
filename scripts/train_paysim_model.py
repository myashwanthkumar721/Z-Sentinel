"""
Z-Sentinel - PaySim fraud model training.

------------
Trains a dedicated XGBoost fraud detection model using the
preprocessed PaySim dataset.

Design goals:
- Keep the existing Z-Sentinel model untouched.
- Use a chronological 80/20 train/test split.
- Keep all fraud examples in the training portion.
- Sample normal transactions to control memory and training time.
- Evaluate on the complete chronological test portion.
- Save model metadata for safe future integration.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from xgboost import XGBClassifier


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

MODEL_DIR = BASE_DIR / "models"

MODEL_FILE = (
    MODEL_DIR
    / "paysim_fraud_model.pkl"
)

FEATURE_FILE = (
    MODEL_DIR
    / "paysim_feature_columns.json"
)

METRICS_FILE = (
    MODEL_DIR
    / "paysim_model_metrics.json"
)


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

CHUNK_SIZE = 250_000

TRAIN_RATIO = 0.80

# Keep all fraud rows, but only this fraction of normal rows
# in the training data.
NORMAL_SAMPLE_FRACTION = 0.10

RANDOM_STATE = 42

TARGET_COLUMN = "is_fraud"

FEATURE_COLUMNS = [
    "step",
    "transaction_type",
    "amount",
    "sender_balance_before",
    "sender_balance_after",
    "sender_balance_change",
    "sender_balance_error",
    "sender_zero_balance_after",
    "receiver_balance_before",
    "receiver_balance_after",
    "receiver_balance_change",
    "receiver_balance_error",
    "receiver_zero_balance_before",
    "amount_to_sender_balance_ratio",
    "amount_exceeds_sender_balance",
    "hour_proxy",
    "day_proxy",
    "is_flagged_fraud",
    "origin_is_customer",
    "destination_is_customer",
    "same_account_type",
]


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def validate_dataset() -> None:
    """Validate that the processed PaySim file exists."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Processed PaySim dataset not found:\n{DATA_FILE}"
        )

    if not FEATURE_COLUMNS:
        raise ValueError(
            "FEATURE_COLUMNS cannot be empty."
        )


def calculate_split_rows() -> tuple[int, int]:
    """
    Determine the chronological train/test row boundary.

    Uses only the target column so the complete feature matrix
    does not need to be loaded just to determine the row count.
    """

    print("Counting PaySim rows...")

    row_count = 0

    for chunk in pd.read_csv(
        DATA_FILE,
        usecols=[TARGET_COLUMN],
        chunksize=CHUNK_SIZE,
    ):
        row_count += len(chunk)

    train_rows = int(
        row_count * TRAIN_RATIO
    )

    test_rows = (
        row_count
        - train_rows
    )

    print(
        f"Total rows : {row_count:,}"
    )

    print(
        f"Train rows : {train_rows:,}"
    )

    print(
        f"Test rows  : {test_rows:,}"
    )

    return train_rows, test_rows


def load_train_data(
    train_rows: int,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Load the chronological training portion.

    All fraud rows are retained.

    Only a fraction of normal rows are retained to keep the
    training dataset manageable.
    """

    print()
    print("=" * 70)
    print("BUILDING TRAINING DATA")
    print("=" * 70)

    selected_frames = []

    rows_seen = 0
    fraud_seen = 0
    normal_seen = 0

    fraud_selected = 0
    normal_selected = 0

    rng = np.random.default_rng(
        RANDOM_STATE
    )

    usecols = FEATURE_COLUMNS + [
        TARGET_COLUMN
    ]

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            DATA_FILE,
            usecols=usecols,
            chunksize=CHUNK_SIZE,
        ),
        start=1,
    ):

        remaining = (
            train_rows
            - rows_seen
        )

        if remaining <= 0:
            break

        if len(chunk) > remaining:
            chunk = chunk.iloc[
                :remaining
            ].copy()

        rows_seen += len(chunk)

        fraud_mask = (
            chunk[TARGET_COLUMN] == 1
        )

        normal_mask = (
            chunk[TARGET_COLUMN] == 0
        )

        fraud_count = int(
            fraud_mask.sum()
        )

        normal_count = int(
            normal_mask.sum()
        )

        fraud_seen += fraud_count
        normal_seen += normal_count

        fraud_part = chunk.loc[
            fraud_mask
        ]

        normal_part = chunk.loc[
            normal_mask
        ]

        # Keep every fraud example.
        if not fraud_part.empty:
            selected_frames.append(
                fraud_part
            )

            fraud_selected += len(
                fraud_part
            )

        # Sample only part of the normal population.
        if not normal_part.empty:

            sample_size = int(
                len(normal_part)
                * NORMAL_SAMPLE_FRACTION
            )

            if sample_size > 0:

                selected_indices = rng.choice(
                    len(normal_part),
                    size=sample_size,
                    replace=False,
                )

                sampled_normal = (
                    normal_part.iloc[
                        selected_indices
                    ]
                )

                selected_frames.append(
                    sampled_normal
                )

                normal_selected += len(
                    sampled_normal
                )

        print(
            f"Chunk {chunk_number:02d} | "
            f"rows={rows_seen:,} | "
            f"fraud={fraud_seen:,} | "
            f"normal={normal_seen:,}"
        )

    if not selected_frames:
        raise RuntimeError(
            "No training data was selected."
        )

    train_df = pd.concat(
        selected_frames,
        ignore_index=True,
    )

    # Separate features and target.
    X_train = train_df[
        FEATURE_COLUMNS
    ].copy()

    y_train = train_df[
        TARGET_COLUMN
    ].copy()

    # Free the combined frame as soon as possible.
    del train_df

    print()
    print(
        f"Training rows selected : {len(y_train):,}"
    )

    print(
        f"Training fraud rows    : "
        f"{fraud_selected:,}"
    )

    print(
        f"Training normal rows   : "
        f"{normal_selected:,}"
    )

    fraud_rate = (
        y_train.mean() * 100
    )

    print(
        f"Training fraud rate    : "
        f"{fraud_rate:.4f}%"
    )

    return X_train, y_train


def load_test_data(
    train_rows: int,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Load the complete chronological test portion.

    Unlike training, the test set is NOT downsampled.
    """

    print()
    print("=" * 70)
    print("BUILDING TEST DATA")
    print("=" * 70)

    frames = []

    rows_seen = 0

    usecols = FEATURE_COLUMNS + [
        TARGET_COLUMN
    ]

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

        # Entire chunk is before test region.
        if chunk_end <= train_rows:
            continue

        # Remove the training portion if this chunk
        # crosses the split boundary.
        if chunk_start < train_rows:
            offset = (
                train_rows
                - chunk_start
            )

            chunk = chunk.iloc[
                offset:
            ].copy()

        if not chunk.empty:
            frames.append(chunk)

        print(
            f"Chunk {chunk_number:02d} | "
            f"test rows collected="
            f"{sum(len(frame) for frame in frames):,}"
        )

    if not frames:
        raise RuntimeError(
            "No test data was loaded."
        )

    test_df = pd.concat(
        frames,
        ignore_index=True,
    )

    X_test = test_df[
        FEATURE_COLUMNS
    ].copy()

    y_test = test_df[
        TARGET_COLUMN
    ].copy()

    del test_df

    print()
    print(
        f"Test rows  : {len(y_test):,}"
    )

    print(
        f"Test fraud : "
        f"{int(y_test.sum()):,}"
    )

    print(
        f"Test normal: "
        f"{int((y_test == 0).sum()):,}"
    )

    print(
        f"Test fraud rate: "
        f"{y_test.mean() * 100:.4f}%"
    )

    return X_test, y_test


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> XGBClassifier:
    """Train the PaySim XGBoost classifier."""

    print()
    print("=" * 70)
    print("TRAINING XGBOOST FRAUD MODEL")
    print("=" * 70)

    fraud_count = int(
        y_train.sum()
    )

    normal_count = int(
        (y_train == 0).sum()
    )

    if fraud_count == 0:
        raise ValueError(
            "Training data contains no fraud examples."
        )

    scale_pos_weight = (
        normal_count
        / fraud_count
    )

    print(
        f"Fraud samples : {fraud_count:,}"
    )

    print(
        f"Normal samples: {normal_count:,}"
    )

    print(
        f"scale_pos_weight: "
        f"{scale_pos_weight:.4f}"
    )

    model = XGBClassifier(
        n_estimators=300,
        max_depth=8,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=3,
        gamma=0.0,
        reg_alpha=0.0,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="aucpr",
        scale_pos_weight=scale_pos_weight,
        tree_method="hist",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    start = time.time()

    model.fit(
        X_train,
        y_train,
        verbose=False,
    )

    elapsed = (
        time.time()
        - start
    )

    print()
    print(
        f"Training completed in "
        f"{elapsed:.2f} seconds."
    )

    return model


def evaluate_model(
    model: XGBClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    """Evaluate the trained model."""

    print()
    print("=" * 70)
    print("EVALUATING PAYSIM MODEL")
    print("=" * 70)

    probabilities = (
        model.predict_proba(
            X_test
        )[:, 1]
    )

    predictions = (
        probabilities >= 0.50
    ).astype(int)

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    pr_auc = average_precision_score(
        y_test,
        probabilities,
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
    )

    tn, fp, fn, tp = (
        matrix.ravel()
    )

    metrics = {
        "dataset": "PaySim",
        "train_ratio": TRAIN_RATIO,
        "normal_sample_fraction": (
            NORMAL_SAMPLE_FRACTION
        ),
        "classification_threshold": 0.50,
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
        "test_rows": int(len(y_test)),
        "test_fraud_rows": int(
            y_test.sum()
        ),
        "test_normal_rows": int(
            (y_test == 0).sum()
        ),
    }

    print()
    print(
        f"Accuracy : {accuracy:.4f}"
    )

    print(
        f"Precision: {precision:.4f}"
    )

    print(
        f"Recall   : {recall:.4f}"
    )

    print(
        f"F1 Score : {f1:.4f}"
    )

    print(
        f"ROC-AUC  : {roc_auc:.4f}"
    )

    print(
        f"PR-AUC   : {pr_auc:.4f}"
    )

    print()
    print("Confusion Matrix:")
    print(matrix)

    print()
    print(
        "TN:", tn
    )

    print(
        "FP:", fp
    )

    print(
        "FN:", fn
    )

    print(
        "TP:", tp
    )

    return metrics


def save_artifacts(
    model: XGBClassifier,
    metrics: dict,
) -> None:
    """Save the model and its metadata."""

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        model,
        MODEL_FILE,
    )

    with FEATURE_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            FEATURE_COLUMNS,
            file,
            indent=2,
        )

    with METRICS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            indent=2,
        )

    print()
    print("=" * 70)
    print("MODEL ARTIFACTS SAVED")
    print("=" * 70)

    print(
        f"Model   : {MODEL_FILE}"
    )

    print(
        f"Features: {FEATURE_FILE}"
    )

    print(
        f"Metrics : {METRICS_FILE}"
    )


def main() -> None:
    """Run the complete PaySim model training pipeline."""

    print("=" * 70)
    print("Z-SENTINEL - PAYSIM FRAUD MODEL")
    print("=" * 70)
    print()

    validate_dataset()

    train_rows, _ = (
        calculate_split_rows()
    )

    X_train, y_train = (
        load_train_data(
            train_rows
        )
    )

    X_test, y_test = (
        load_test_data(
            train_rows
        )
    )

    model = train_model(
        X_train,
        y_train,
    )

    metrics = evaluate_model(
        model,
        X_test,
        y_test,
    )

    save_artifacts(
        model,
        metrics,
    )

    print()
    print("=" * 70)
    print("PAYSIM MODEL TRAINING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()