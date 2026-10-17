"""
Z-Sentinel - PaySim predictor validation.

Validates the PaySim predictor against real rows from the
processed PaySim dataset.

This script does not modify any model or project files.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.detection.paysim_predictor import (
    predict_paysim,
)


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "paysim_features.csv"
)

RAW_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "PS_20174392719_1491204439457_log.csv"
)


def validate_files() -> None:

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Processed PaySim file not found:\n{DATA_FILE}"
        )

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Raw PaySim file not found:\n{RAW_FILE}"
        )


def load_sample_transactions() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:

    print("=" * 70)
    print("LOADING REAL PAYSIM TRANSACTIONS")
    print("=" * 70)

    fraud_rows = []
    normal_rows = []

    # Read only enough rows to find representative examples.
    #
    # Fraud is rare in PaySim, so we scan chunks until we
    # have enough examples of both classes.

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            RAW_FILE,
            chunksize=250_000,
        ),
        start=1,
    ):

        fraud = chunk[
            chunk["isFraud"] == 1
        ]

        normal = chunk[
            chunk["isFraud"] == 0
        ]

        if not fraud.empty:
            fraud_rows.append(
                fraud.head(5)
            )

        if not normal.empty:
            normal_rows.append(
                normal.head(5)
            )

        fraud_count = sum(
            len(frame)
            for frame in fraud_rows
        )

        normal_count = sum(
            len(frame)
            for frame in normal_rows
        )

        print(
            f"Chunk {chunk_number:02d} | "
            f"fraud samples={fraud_count} | "
            f"normal samples={normal_count}"
        )

        if (
            fraud_count >= 5
            and normal_count >= 5
        ):
            break

    if not fraud_rows:
        raise RuntimeError(
            "No fraud transactions found."
        )

    if not normal_rows:
        raise RuntimeError(
            "No normal transactions found."
        )

    fraud_df = pd.concat(
        fraud_rows,
        ignore_index=True,
    ).head(5)

    normal_df = pd.concat(
        normal_rows,
        ignore_index=True,
    ).head(5)

    return fraud_df, normal_df


def convert_transaction(
    row: pd.Series,
) -> dict:

    return {
        "step": row["step"],
        "type": row["type"],
        "amount": row["amount"],
        "nameOrig": row["nameOrig"],
        "oldbalanceOrg": row["oldbalanceOrg"],
        "newbalanceOrig": row["newbalanceOrig"],
        "nameDest": row["nameDest"],
        "oldbalanceDest": row["oldbalanceDest"],
        "newbalanceDest": row["newbalanceDest"],
        "isFlaggedFraud": row["isFlaggedFraud"],
    }


def run_test_group(
    dataframe: pd.DataFrame,
    expected_label: int,
    label_name: str,
) -> list[float]:

    print()
    print("=" * 70)
    print(f"{label_name.upper()} TRANSACTIONS")
    print("=" * 70)

    probabilities = []

    for index, (_, row) in enumerate(
        dataframe.iterrows(),
        start=1,
    ):

        transaction = convert_transaction(
            row
        )

        result = predict_paysim(
            transaction
        )

        probability = (
            result["ml_probability"]
        )

        probabilities.append(
            probability
        )

        predicted_label = int(
            probability >= 0.50
        )

        status = (
            "CORRECT"
            if predicted_label == expected_label
            else "CHECK"
        )

        print(
            f"{index}. "
            f"type={row['type']:<10} "
            f"amount={row['amount']:>12.2f} "
            f"actual={int(row['isFraud'])} "
            f"probability={probability:.6f} "
            f"predicted={predicted_label} "
            f"[{status}]"
        )

    return probabilities


def main() -> None:

    print("=" * 70)
    print("Z-SENTINEL - PAYSIM PREDICTOR VALIDATION")
    print("=" * 70)

    validate_files()

    fraud_df, normal_df = (
        load_sample_transactions()
    )

    fraud_probabilities = run_test_group(
        fraud_df,
        expected_label=1,
        label_name="Fraud",
    )

    normal_probabilities = run_test_group(
        normal_df,
        expected_label=0,
        label_name="Normal",
    )

    print()
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    print(
        f"Fraud samples tested : "
        f"{len(fraud_probabilities)}"
    )

    print(
        f"Normal samples tested: "
        f"{len(normal_probabilities)}"
    )

    print()
    print(
        f"Average fraud probability: "
        f"{sum(fraud_probabilities) / len(fraud_probabilities):.6f}"
    )

    print(
        f"Average normal probability: "
        f"{sum(normal_probabilities) / len(normal_probabilities):.6f}"
    )

    fraud_correct = sum(
        probability >= 0.50
        for probability in fraud_probabilities
    )

    normal_correct = sum(
        probability < 0.50
        for probability in normal_probabilities
    )

    print()
    print(
        f"Fraud correctly detected: "
        f"{fraud_correct}/{len(fraud_probabilities)}"
    )

    print(
        f"Normal correctly classified: "
        f"{normal_correct}/{len(normal_probabilities)}"
    )

    print()
    print(
        "PaySim predictor validation complete."
    )

    print(
        "No model files were modified."
    )


if __name__ == "__main__":
    main()

