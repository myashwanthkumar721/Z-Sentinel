"""
Z-Sentinel - PaySim Processor Integration Test.

Tests the complete TransactionProcessor using
the PaySim fraud model.

This verifies:

    PaySim model
        ↓
    Model Router
        ↓
    Transaction Processor
        ↓
    Anomaly Detection
        ↓
    Network Intelligence
        ↓
    Fraud-Ring Intelligence
        ↓
    Risk Engine
        ↓
    Decision Engine
"""

from pathlib import Path

import pandas as pd

from src.streaming.processor import TransactionProcessor


BASE_DIR = Path(__file__).resolve().parent.parent

PAYSIM_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "PS_20174392719_1491204439457_log.csv"
)


def convert_transaction(row: pd.Series) -> dict:
    """Convert PaySim row into Z-Sentinel transaction format."""

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

        # Z-Sentinel contextual fields
        "transaction_id": "PAYSIM-TEST",
        "account_id": str(row["nameOrig"]),
        "device_id": "DEVICE-PAYSIM-TEST",
        "ip_address": "10.0.0.1",
        "merchant_id": "MERCHANT-PAYSIM-TEST",

        "transactions_last_1h": 0,
        "failed_attempts": 0,
        "is_new_device": 0,
        "is_international": 0,
        "merchant_risk": 0.0,
        "ip_risk": 0.0,
    }


def get_samples() -> tuple[pd.Series, pd.Series]:
    """Return one real fraud and one real normal transaction."""

    for chunk in pd.read_csv(
        PAYSIM_FILE,
        chunksize=250_000,
    ):
        fraud = chunk[
            chunk["isFraud"] == 1
        ]

        normal = chunk[
            chunk["isFraud"] == 0
        ]

        if not fraud.empty and not normal.empty:
            return (
                fraud.iloc[0],
                normal.iloc[0],
            )

    raise RuntimeError(
        "Could not find fraud and normal samples."
    )


def print_result(
    label: str,
    result: dict,
) -> None:
    """Print important processor output."""

    print("\n" + "=" * 70)
    print(label)
    print("=" * 70)

    print(
        f"Model            : "
        f"{result['prediction_model']}"
    )

    print(
        f"Source           : "
        f"{result['prediction_source']}"
    )

    print(
        f"ML probability   : "
        f"{result['ml_probability']:.6f}"
    )

    print(
        f"Anomaly score    : "
        f"{result['anomaly_score']:.6f}"
    )

    print(
        f"Network score    : "
        f"{result['network_score']:.6f}"
    )

    print(
        f"Fraud-ring score : "
        f"{result['fraud_ring_score']:.6f}"
    )

    print(
        f"Risk score       : "
        f"{result['risk_score']:.2f}"
    )

    print(
        f"Base decision    : "
        f"{result['base_decision']}"
    )

    print(
        f"Final decision   : "
        f"{result['decision']}"
    )

    print(
        f"Reasons          : "
        f"{result['reasons']}"
    )


def main() -> None:
    print("=" * 70)
    print("Z-SENTINEL - PAYSIM PROCESSOR INTEGRATION TEST")
    print("=" * 70)

    fraud_row, normal_row = get_samples()

    # --------------------------------------------------------
    # Create processor in PaySim mode
    # --------------------------------------------------------

    processor = TransactionProcessor(
        model_name="paysim"
    )

    print(
        f"\nSelected model: "
        f"{processor.get_model_name()}"
    )

    # --------------------------------------------------------
    # Process real fraud transaction
    # --------------------------------------------------------

    fraud_transaction = convert_transaction(
        fraud_row
    )

    fraud_result = processor.process(
        fraud_transaction,
        save_history=False,
    )

    print_result(
        "REAL PAYSIM FRAUD",
        fraud_result,
    )

    # --------------------------------------------------------
    # Process real normal transaction
    # --------------------------------------------------------

    normal_transaction = convert_transaction(
        normal_row
    )

    normal_result = processor.process(
        normal_transaction,
        save_history=False,
    )

    print_result(
        "REAL PAYSIM NORMAL",
        normal_result,
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    fraud_model_ok = (
        fraud_result["prediction_model"]
        == "paysim_fraud_model"
    )

    normal_model_ok = (
        normal_result["prediction_model"]
        == "paysim_fraud_model"
    )

    fraud_probability_ok = (
        fraud_result["ml_probability"] >= 0.90
    )

    normal_probability_ok = (
        normal_result["ml_probability"] < 0.90
    )

    print(
        f"Fraud uses PaySim model : "
        f"{fraud_model_ok}"
    )

    print(
        f"Normal uses PaySim model: "
        f"{normal_model_ok}"
    )

    print(
        f"Fraud ML >= 0.90        : "
        f"{fraud_probability_ok}"
    )

    print(
        f"Normal ML < 0.90        : "
        f"{normal_probability_ok}"
    )

    all_passed = all(
        [
            fraud_model_ok,
            normal_model_ok,
            fraud_probability_ok,
            normal_probability_ok,
        ]
    )

    print(
        "\nOverall result: "
        f"{'PASS' if all_passed else 'FAIL'}"
    )


if __name__ == "__main__":
    main()