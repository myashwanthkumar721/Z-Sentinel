"""
Z-Sentinel - PaySim model robustness audit.

------------
Tests how dependent the PaySim fraud model is on the strongest
balance-derived features.

This script DOES NOT modify the production/demo model.

Removed features:
- sender_zero_balance_after
- sender_balance_error
- amount_exceeds_sender_balance
- sender_balance_change
- sender_balance_after
- is_flagged_fraud

The audit uses the same chronological 80/20 split as the
PaySim training pipeline.
"""

from __future__ import annotations

import time
from pathlib import Path

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


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

CHUNK_SIZE = 250_000

TRAIN_RATIO = 0.80

NORMAL_SAMPLE_FRACTION = 0.10

RANDOM_STATE = 42


# -------------------------------------------------------------------
# Original feature set
# -------------------------------------------------------------------

ALL_FEATURES = [
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
# Features deliberately removed for robustness audit
# -------------------------------------------------------------------

REMOVED_FEATURES = [
    "sender_zero_balance_after",
    "sender_balance_error",
    "amount_exceeds_sender_balance",
    "sender_balance_change",
    "sender_balance_after",
    "is_flagged_fraud",
]


AUDIT_FEATURES = [
    feature
    for feature in ALL_FEATURES
    if feature not in REMOVED_FEATURES
]


TARGET_COLUMN = "is_fraud"


# -------------------------------------------------------------------
# Dataset helpers
# -------------------------------------------------------------------

def validate_dataset() -> None:
    """Check that the processed PaySim dataset exists."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Processed PaySim dataset not found:\n{DATA_FILE}"
        )

    if not AUDIT_FEATURES:
        raise ValueError(
            "Audit feature list is empty."
        )


def count_rows() -> int:
    """Count total dataset rows."""

    total_rows = 0

    for chunk in pd.read_csv(
        DATA_FILE,
        usecols=[TARGET_COLUMN],
        chunksize=CHUNK_SIZE,
    ):
        total_rows += len(chunk)

    return total_rows


def build_train_test_split() -> tuple[int, int]:
    """Calculate chronological train/test boundaries."""

    total_rows = count_rows()

    train_rows = int(
        total_rows * TRAIN_RATIO
    )

    test_rows = (
        total_rows
        - train_rows
    )

    print(
        f"Total rows : {total_rows:,}"
    )

    print(
        f"Train rows : {train_rows:,}"
    )

    print(
        f"Test rows  : {test_rows:,}"
    )

    return train_rows, test_rows


# -------------------------------------------------------------------
# Training data
# -------------------------------------------------------------------

def load_training_data(
    train_rows: int,
) -> tuple[pd.DataFrame, pd.Series]:

    print()
    print("=" * 70)
    print("BUILDING ROBUSTNESS-AUDIT TRAINING DATA")
    print("=" * 70)

    usecols = (
        AUDIT_FEATURES
        + [TARGET_COLUMN]
    )

    selected_frames = []

    rows_seen = 0

    fraud_selected = 0
    normal_selected = 0

    rng = np.random.default_rng(
        RANDOM_STATE
    )

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

        # Sample normal examples.
        if not normal_part.empty:

            sample_size = int(
                len(normal_part)
                * NORMAL_SAMPLE_FRACTION
            )

            if sample_size > 0:

                indices = rng.choice(
                    len(normal_part),
                    size=sample_size,
                    replace=False,
                )

                sampled_normal = (
                    normal_part.iloc[
                        indices
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
            f"rows={rows_seen:,}"
        )

    if not selected_frames:
        raise RuntimeError(
            "No audit training data was selected."
        )

    train_df = pd.concat(
        selected_frames,
        ignore_index=True,
    )

    X_train = train_df[
        AUDIT_FEATURES
    ].copy()

    y_train = train_df[
        TARGET_COLUMN
    ].copy()

    del train_df

    print()
    print(
        f"Audit training rows : "
        f"{len(y_train):,}"
    )

    print(
        f"Fraud rows          : "
        f"{fraud_selected:,}"
    )

    print(
        f"Normal rows         : "
        f"{normal_selected:,}"
    )

    print(
        f"Fraud rate           : "
        f"{y_train.mean() * 100:.4f}%"
    )

    return X_train, y_train


# -------------------------------------------------------------------
# Test data
# -------------------------------------------------------------------

def load_test_data(
    train_rows: int,
) -> tuple[pd.DataFrame, pd.Series]:

    print()
    print("=" * 70)
    print("BUILDING ROBUSTNESS-AUDIT TEST DATA")
    print("=" * 70)

    usecols = (
        AUDIT_FEATURES
        + [TARGET_COLUMN]
    )

    frames = []

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

        if chunk_end <= train_rows:
            continue

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

        collected = sum(
            len(frame)
            for frame in frames
        )

        print(
            f"Chunk {chunk_number:02d} | "
            f"test rows={collected:,}"
        )

    if not frames:
        raise RuntimeError(
            "No audit test data was loaded."
        )

    test_df = pd.concat(
        frames,
        ignore_index=True,
    )

    X_test = test_df[
        AUDIT_FEATURES
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

    return X_test, y_test


# -------------------------------------------------------------------
# Model
# -------------------------------------------------------------------

def train_audit_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> XGBClassifier:

    print()
    print("=" * 70)
    print("TRAINING ROBUSTNESS-AUDIT MODEL")
    print("=" * 70)

    fraud_count = int(
        y_train.sum()
    )

    normal_count = int(
        (y_train == 0).sum()
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


# -------------------------------------------------------------------
# Evaluation
# -------------------------------------------------------------------

def evaluate_model(
    model: XGBClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:

    print()
    print("=" * 70)
    print("ROBUSTNESS-AUDIT RESULTS")
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
        f"TN: {tn}"
    )

    print(
        f"FP: {fp}"
    )

    print(
        f"FN: {fn}"
    )

    print(
        f"TP: {tp}"
    )

    return {
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
    }


# -------------------------------------------------------------------
# Feature importance
# -------------------------------------------------------------------

def show_feature_importance(
    model: XGBClassifier,
) -> None:

    print()
    print("=" * 70)
    print("AUDIT MODEL FEATURE IMPORTANCE")
    print("=" * 70)

    pairs = sorted(
        zip(
            AUDIT_FEATURES,
            model.feature_importances_,
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    for index, (
        feature,
        importance,
    ) in enumerate(
        pairs,
        start=1,
    ):

        print(
            f"{index:02d}. "
            f"{feature:<35} "
            f"{importance:.6f}"
        )


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main() -> None:

    print("=" * 70)
    print("Z-SENTINEL - PAYSIM ROBUSTNESS AUDIT")
    print("=" * 70)

    print()
    print("Removed features:")

    for feature in REMOVED_FEATURES:
        print(
            f"  - {feature}"
        )

    print()
    print("Remaining features:")

    for feature in AUDIT_FEATURES:
        print(
            f"  + {feature}"
        )

    validate_dataset()

    train_rows, _ = (
        build_train_test_split()
    )

    X_train, y_train = (
        load_training_data(
            train_rows
        )
    )

    X_test, y_test = (
        load_test_data(
            train_rows
        )
    )

    model = train_audit_model(
        X_train,
        y_train,
    )

    metrics = evaluate_model(
        model,
        X_test,
        y_test,
    )

    show_feature_importance(
        model
    )

    print()
    print("=" * 70)
    print("ROBUSTNESS AUDIT COMPLETE")
    print("=" * 70)

    print()
    print(
        "Important: this audit model was NOT saved "
        "and does NOT replace the existing PaySim model."
    )

    print()
    print("Metrics summary:")

    for key, value in metrics.items():

        if isinstance(
            value,
            float,
        ):
            print(
                f"{key}: {value:.4f}"
            )
        else:
            print(
                f"{key}: {value}"
            )


if __name__ == "__main__":
    main()