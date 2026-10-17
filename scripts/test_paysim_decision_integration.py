"""
Z-Sentinel - PaySim Final Decision Integration Test

Tests the complete PaySim intelligence path:

    Real PaySim transaction
            ↓
    PaySim fraud predictor
            ↓
       Risk Engine
            ↓
     Decision Engine
            ↓
      Final Decision

This script does NOT modify:
    - live processor
    - dashboard
    - trained models
    - risk_engine.py
    - decision_engine.py
"""

from pathlib import Path

import pandas as pd

from src.detection.paysim_predictor import predict_paysim
from src.risk.risk_engine import evaluate_risk
from src.risk.decision_engine import apply_decision_policy


BASE_DIR = Path(__file__).resolve().parent.parent

PAYSIM_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "PS_20174392719_1491204439457_log.csv"
)


def convert_transaction(row: pd.Series) -> dict:
    """Convert a raw PaySim row into predictor input."""

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


def build_z_sentinel_context(transaction: dict) -> dict:
    """
    Add neutral contextual signals required by the
    existing Z-Sentinel risk engine.
    """

    transaction = dict(transaction)

    transaction.update(
        {
            "transaction_id": "PAYSIM-INTEGRATION",
            "account_id": transaction["nameOrig"],
            "device_id": "PAYSIM-DEVICE",
            "ip_address": "PAYSIM-IP",
            "merchant_id": "PAYSIM-MERCHANT",
            "transactions_last_1h": 0,
            "is_new_device": 0,
            "is_international": 0,
            "failed_attempts": 0,
            "merchant_risk": 0.0,
            "ip_risk": 0.0,
        }
    )

    return transaction


def evaluate_transaction(
    transaction: dict,
) -> dict:
    """Run one transaction through PaySim + risk + policy."""

    prediction = predict_paysim(transaction)

    ml_probability = float(
        prediction["ml_probability"]
    )

    risk_result = evaluate_risk(
        transaction=transaction,
        ml_probability=ml_probability,
        anomaly_score=0.0,
        network_score=0.0,
        fraud_ring_score=0.0,
        network_degree=0,
        connected_accounts=[],
    )

    base_decision = risk_result["decision"]

    final_decision = apply_decision_policy(
        base_decision=base_decision,
        ml_probability=ml_probability,
    )

    return {
        "ml_probability": ml_probability,
        "risk_score": float(
            risk_result["risk_score"]
        ),
        "base_decision": base_decision,
        "final_decision": final_decision,
    }


def main() -> None:
    print("=" * 78)
    print("Z-SENTINEL - PAYSIM FINAL DECISION INTEGRATION TEST")
    print("=" * 78)

    print("\nLoading real PaySim transactions...")

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

    # ========================================================
    # FRAUD TRANSACTIONS
    # ========================================================

    print("\n" + "=" * 78)
    print("REAL FRAUD TRANSACTIONS")
    print("=" * 78)

    fraud_final_decisions = []

    for index, row in enumerate(
        fraud_samples,
        start=1,
    ):
        transaction = convert_transaction(row)
        transaction = build_z_sentinel_context(
            transaction
        )

        result = evaluate_transaction(
            transaction
        )

        fraud_final_decisions.append(
            result["final_decision"]
        )

        print(
            f"\n{index}. "
            f"type={row['type']:<10} "
            f"amount={float(row['amount']):>12.2f}"
        )

        print(
            f"   ML probability : "
            f"{result['ml_probability']:.6f}"
        )

        print(
            f"   Risk score     : "
            f"{result['risk_score']:.2f}"
        )

        print(
            f"   Base decision  : "
            f"{result['base_decision']}"
        )

        print(
            f"   FINAL decision : "
            f"{result['final_decision']}"
        )

    # ========================================================
    # NORMAL TRANSACTIONS
    # ========================================================

    print("\n" + "=" * 78)
    print("REAL NORMAL TRANSACTIONS")
    print("=" * 78)

    normal_final_decisions = []

    for index, row in enumerate(
        normal_samples,
        start=1,
    ):
        transaction = convert_transaction(row)
        transaction = build_z_sentinel_context(
            transaction
        )

        result = evaluate_transaction(
            transaction
        )

        normal_final_decisions.append(
            result["final_decision"]
        )

        print(
            f"\n{index}. "
            f"type={row['type']:<10} "
            f"amount={float(row['amount']):>12.2f}"
        )

        print(
            f"   ML probability : "
            f"{result['ml_probability']:.6f}"
        )

        print(
            f"   Risk score     : "
            f"{result['risk_score']:.2f}"
        )

        print(
            f"   Base decision  : "
            f"{result['base_decision']}"
        )

        print(
            f"   FINAL decision : "
            f"{result['final_decision']}"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 78)
    print("FINAL INTEGRATION SUMMARY")
    print("=" * 78)

    print(
        f"\nFraud samples tested : "
        f"{len(fraud_final_decisions)}"
    )

    print(
        f"Normal samples tested: "
        f"{len(normal_final_decisions)}"
    )

    print(
        "\nFraud final decisions:"
    )

    for decision in sorted(
        set(fraud_final_decisions)
    ):
        print(
            f"  {decision}: "
            f"{fraud_final_decisions.count(decision)}"
        )

    print(
        "\nNormal final decisions:"
    )

    for decision in sorted(
        set(normal_final_decisions)
    ):
        print(
            f"  {decision}: "
            f"{normal_final_decisions.count(decision)}"
        )

    fraud_escalated = sum(
        decision in {"VERIFY", "HOLD"}
        for decision in fraud_final_decisions
    )

    print(
        f"\nFraud transactions escalated: "
        f"{fraud_escalated}/"
        f"{len(fraud_final_decisions)}"
    )

    normal_allowed = sum(
        decision == "ALLOW"
        for decision in normal_final_decisions
    )

    print(
        f"Normal transactions remaining ALLOW: "
        f"{normal_allowed}/"
        f"{len(normal_final_decisions)}"
    )

    print("\n" + "=" * 78)
    print("PAYSim → RISK ENGINE → DECISION ENGINE TEST COMPLETE")
    print("=" * 78)

    print(
        "No live pipeline or model files were modified."
    )


if __name__ == "__main__":
    main()