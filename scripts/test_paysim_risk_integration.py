"""
Z-Sentinel - PaySim + Risk Engine Integration Test.

-----------------
Tests the PaySim fraud probability flowing into the existing
Z-Sentinel risk engine.

This script does NOT modify the live streaming processor,
dashboard, or production models.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.detection.paysim_predictor import (
    predict_paysim,
)

from src.risk.risk_engine import (
    evaluate_risk,
)


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "PS_20174392719_1491204439457_log.csv"
)


def load_examples() -> tuple[
    pd.Series,
    pd.Series,
]:

    print("=" * 70)
    print("LOADING PAYSim EXAMPLES")
    print("=" * 70)

    for chunk in pd.read_csv(
        RAW_FILE,
        chunksize=250_000,
    ):

        fraud_rows = chunk[
            chunk["isFraud"] == 1
        ]

        normal_rows = chunk[
            chunk["isFraud"] == 0
        ]

        if (
            not fraud_rows.empty
            and not normal_rows.empty
        ):

            return (
                fraud_rows.iloc[0],
                normal_rows.iloc[0],
            )

    raise RuntimeError(
        "Unable to find both fraud and normal examples."
    )


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

        # Z-Sentinel risk-engine fields.
        #
        # PaySim does not contain these signals directly,
        # so this integration test keeps them neutral.
        "transactions_last_1h": 0,
        "is_new_device": 0,
        "is_international": 0,
        "failed_attempts": 0,
        "merchant_risk": 0.0,
        "ip_risk": 0.0,
    }


def evaluate_transaction(
    row: pd.Series,
    label: str,
) -> dict:

    transaction = convert_transaction(
        row
    )

    paysim_result = predict_paysim(
        transaction
    )

    ml_probability = (
        paysim_result["ml_probability"]
    )

    # Neutral values for signals that PaySim
    # does not directly provide.
    anomaly_score = 0.0
    network_score = 0.0
    fraud_ring_score = 0.0

    risk_result = evaluate_risk(
        transaction=transaction,
        ml_probability=ml_probability,
        anomaly_score=anomaly_score,
        network_score=network_score,
        fraud_ring_score=fraud_ring_score,
        network_degree=0,
        connected_accounts=[],
    )

    print()
    print("=" * 70)
    print(f"{label.upper()} TRANSACTION")
    print("=" * 70)

    print(
        f"Actual PaySim label : "
        f"{int(row['isFraud'])}"
    )

    print(
        f"Transaction type    : "
        f"{row['type']}"
    )

    print(
        f"Amount              : "
        f"{row['amount']:.2f}"
    )

    print(
        f"ML probability      : "
        f"{ml_probability:.6f}"
    )

    print(
        f"Risk score          : "
        f"{risk_result['risk_score']:.2f}"
    )

    print(
        f"Decision             : "
        f"{risk_result['decision']}"
    )

    print()
    print("Signals:")

    for name, value in (
        risk_result["signals"]
        .items()
    ):

        print(
            f"  {name:<20} "
            f"{value:.4f}"
        )

    print()
    print("Reasons:")

    for reason in (
        risk_result["reasons"]
    ):

        print(
            f"  - {reason}"
        )

    return {
        "actual_label": int(
            row["isFraud"]
        ),
        "ml_probability": ml_probability,
        "risk_score": risk_result[
            "risk_score"
        ],
        "decision": risk_result[
            "decision"
        ],
        "result": risk_result,
    }


def main() -> None:

    print("=" * 70)
    print("Z-SENTINEL - PAYSIM RISK INTEGRATION TEST")
    print("=" * 70)

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"PaySim raw dataset not found:\n{RAW_FILE}"
        )

    fraud_row, normal_row = (
        load_examples()
    )

    fraud_result = evaluate_transaction(
        fraud_row,
        "Fraud",
    )

    normal_result = evaluate_transaction(
        normal_row,
        "Normal",
    )

    print()
    print("=" * 70)
    print("INTEGRATION SUMMARY")
    print("=" * 70)

    print(
        f"Fraud ML probability : "
        f"{fraud_result['ml_probability']:.6f}"
    )

    print(
        f"Fraud risk score     : "
        f"{fraud_result['risk_score']:.2f}"
    )

    print(
        f"Fraud decision       : "
        f"{fraud_result['decision']}"
    )

    print()

    print(
        f"Normal ML probability: "
        f"{normal_result['ml_probability']:.6f}"
    )

    print(
        f"Normal risk score    : "
        f"{normal_result['risk_score']:.2f}"
    )

    print(
        f"Normal decision      : "
        f"{normal_result['decision']}"
    )

    print()
    print(
        "PaySim → Z-Sentinel risk-engine integration test complete."
    )

    print(
        "No live pipeline or model files were modified."
    )


if __name__ == "__main__":
    main()