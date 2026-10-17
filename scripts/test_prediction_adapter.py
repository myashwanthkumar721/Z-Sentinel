"""
Z-Sentinel - Prediction Adapter Validation

Validates the common prediction adapter using real PaySim
transactions.

This script does not modify:
    - trained models
    - live processor
    - dashboard
    - risk engine
"""


from pathlib import Path

import pandas as pd

from src.detection.prediction_adapter import (
    predict_with_paysim,
)


BASE_DIR = Path(__file__).resolve().parent.parent

PAYSIM_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "PS_20174392719_1491204439457_log.csv"
)


def convert_transaction(row: pd.Series) -> dict:
    """Convert a PaySim row into predictor input."""

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


def collect_samples() -> tuple[list[pd.Series], list[pd.Series]]:
    """Collect three fraud and three normal PaySim rows."""

    fraud_samples = []
    normal_samples = []

    for chunk in pd.read_csv(
        PAYSIM_FILE,
        chunksize=250_000,
    ):
        if len(fraud_samples) < 3:
            fraud_rows = chunk[
                chunk["isFraud"] == 1
            ]

            for _, row in fraud_rows.iterrows():
                if len(fraud_samples) >= 3:
                    break

                fraud_samples.append(row)

        if len(normal_samples) < 3:
            normal_rows = chunk[
                chunk["isFraud"] == 0
            ]

            for _, row in normal_rows.iterrows():
                if len(normal_samples) >= 3:
                    break

                normal_samples.append(row)

        if (
            len(fraud_samples) >= 3
            and len(normal_samples) >= 3
        ):
            break

    return fraud_samples, normal_samples


def main() -> None:
    print("=" * 78)
    print("Z-SENTINEL - PREDICTION ADAPTER VALIDATION")
    print("=" * 78)

    fraud_samples, normal_samples = (
        collect_samples()
    )

    # ========================================================
    # FRAUD
    # ========================================================

    print("\n" + "=" * 78)
    print("REAL FRAUD TRANSACTIONS")
    print("=" * 78)

    fraud_probabilities = []

    for index, row in enumerate(
        fraud_samples,
        start=1,
    ):
        transaction = convert_transaction(row)

        result = predict_with_paysim(
            transaction
        )

        probability = float(
            result["ml_probability"]
        )

        fraud_probabilities.append(
            probability
        )

        print(
            f"{index}. "
            f"type={row['type']:<10} "
            f"amount={float(row['amount']):>12.2f} "
            f"ML={probability:.6f} "
            f"model={result['model']} "
            f"source={result['prediction_source']}"
        )

    # ========================================================
    # NORMAL
    # ========================================================

    print("\n" + "=" * 78)
    print("REAL NORMAL TRANSACTIONS")
    print("=" * 78)

    normal_probabilities = []

    for index, row in enumerate(
        normal_samples,
        start=1,
    ):
        transaction = convert_transaction(row)

        result = predict_with_paysim(
            transaction
        )

        probability = float(
            result["ml_probability"]
        )

        normal_probabilities.append(
            probability
        )

        print(
            f"{index}. "
            f"type={row['type']:<10} "
            f"amount={float(row['amount']):>12.2f} "
            f"ML={probability:.6f} "
            f"model={result['model']} "
            f"source={result['prediction_source']}"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 78)
    print("ADAPTER VALIDATION SUMMARY")
    print("=" * 78)

    if fraud_probabilities:
        print(
            "\nAverage fraud probability: "
            f"{sum(fraud_probabilities) / len(fraud_probabilities):.6f}"
        )

    if normal_probabilities:
        print(
            "Average normal probability: "
            f"{sum(normal_probabilities) / len(normal_probabilities):.6f}"
        )

    print(
        "\nFraud predictions >= 0.90: "
        f"{sum(p >= 0.90 for p in fraud_probabilities)}/"
        f"{len(fraud_probabilities)}"
    )

    print(
        "Normal predictions < 0.90: "
        f"{sum(p < 0.90 for p in normal_probabilities)}/"
        f"{len(normal_probabilities)}"
    )

    print("\nPrediction adapter validation complete.")
    print("No model files were modified.")


if __name__ == "__main__":
    main()