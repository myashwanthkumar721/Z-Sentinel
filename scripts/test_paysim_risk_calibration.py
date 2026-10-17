"""
Z-Sentinel - PaySim Risk Calibration Test

Purpose:
    Measure how the current Z-Sentinel risk engine responds to different
    PaySim ML fraud probabilities while all other risk signals remain neutral.

This script DOES NOT modify:
    - risk_engine.py
    - live processor
    - dashboard
    - trained models
    - database
"""

from src.risk.risk_engine import evaluate_risk


TEST_PROBABILITIES = [
    0.00,
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
    0.99,
    1.00,
]


def build_neutral_transaction() -> dict:
    """Create a transaction with neutral contextual risk signals."""

    return {
        "transaction_id": "CALIBRATION-001",
        "account_id": "C100001",
        "amount": 1000.0,
        "transactions_last_1h": 0,
        "is_new_device": 0,
        "is_international": 0,
        "failed_attempts": 0,
        "merchant_risk": 0.0,
        "ip_risk": 0.0,
    }


def main() -> None:
    print("=" * 78)
    print("Z-SENTINEL - PAYSIM RISK CALIBRATION TEST")
    print("=" * 78)

    transaction = build_neutral_transaction()

    print("\nAll non-ML signals are neutral:")
    print("  anomaly_score    = 0.0")
    print("  network_score    = 0.0")
    print("  fraud_ring_score = 0.0")
    print("  velocity_score   = 0.0")
    print("  device_score     = 0.0")

    print("\n" + "=" * 78)
    print(
        f"{'ML Probability':<18}"
        f"{'Risk Score':<15}"
        f"{'Decision':<12}"
        f"{'ML Contribution':<18}"
    )
    print("-" * 78)

    results = []

    for probability in TEST_PROBABILITIES:
        result = evaluate_risk(
            transaction=transaction,
            ml_probability=probability,
            anomaly_score=0.0,
            network_score=0.0,
            fraud_ring_score=0.0,
            network_degree=0,
            connected_accounts=[],
        )

        risk_score = result["risk_score"]
        decision = result["decision"]
        ml_contribution = probability * 35.0

        results.append(
            {
                "probability": probability,
                "risk_score": risk_score,
                "decision": decision,
                "ml_contribution": ml_contribution,
            }
        )

        print(
            f"{probability:<18.2f}"
            f"{risk_score:<15.2f}"
            f"{decision:<12}"
            f"{ml_contribution:<18.2f}"
        )

    print("\n" + "=" * 78)
    print("CALIBRATION OBSERVATIONS")
    print("=" * 78)

    first_verify = next(
        (row for row in results if row["decision"] == "VERIFY"),
        None,
    )

    first_hold = next(
        (row for row in results if row["decision"] == "HOLD"),
        None,
    )

    if first_verify:
        print(
            f"\nFirst VERIFY occurs at ML probability "
            f"{first_verify['probability']:.2f}"
        )
    else:
        print("\nVERIFY is never reached using ML alone.")

    if first_hold:
        print(
            f"First HOLD occurs at ML probability "
            f"{first_hold['probability']:.2f}"
        )
    else:
        print("HOLD is never reached using ML alone.")

    print("\nMaximum possible ML-only contribution:")
    print("  35.00 risk points")

    print("\nCurrent decision thresholds:")
    print("  0-39   → ALLOW")
    print("  40-69  → VERIFY")
    print("  70-100 → HOLD")

    print("\n" + "=" * 78)
    print("CALIBRATION TEST COMPLETE")
    print("=" * 78)
    print("No live pipeline or model files were modified.")


if __name__ == "__main__":
    main()