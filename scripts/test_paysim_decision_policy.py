"""
Z-Sentinel - PaySim Decision Policy Test

Tests a proposed policy layer above the existing weighted risk engine.

This script does NOT modify:
    - risk_engine.py
    - live processor
    - dashboard
    - trained models
"""


from src.risk.risk_engine import evaluate_risk


def build_transaction() -> dict:
    """Create a transaction with neutral contextual risk signals."""

    return {
        "transaction_id": "POLICY-001",
        "account_id": "C100001",
        "amount": 1000.0,
        "transactions_last_1h": 0,
        "is_new_device": 0,
        "is_international": 0,
        "failed_attempts": 0,
        "merchant_risk": 0.0,
        "ip_risk": 0.0,
    }


def apply_policy(ml_probability: float, base_decision: str) -> str:
    """
    Proposed policy layer.

    Very high ML confidence prevents an ALLOW decision.
    """

    if ml_probability >= 0.99:
        if base_decision == "ALLOW":
            return "VERIFY"

    elif ml_probability >= 0.90:
        if base_decision == "ALLOW":
            return "VERIFY"

    return base_decision


def main() -> None:
    print("=" * 78)
    print("Z-SENTINEL - PAYSIM DECISION POLICY TEST")
    print("=" * 78)

    transaction = build_transaction()

    probabilities = [
        0.10,
        0.30,
        0.50,
        0.70,
        0.80,
        0.89,
        0.90,
        0.95,
        0.99,
        0.999,
        1.00,
    ]

    print(
        f"\n{'ML Probability':<18}"
        f"{'Base Risk':<14}"
        f"{'Base Decision':<16}"
        f"{'Policy Decision':<16}"
    )

    print("-" * 78)

    for probability in probabilities:
        result = evaluate_risk(
            transaction=transaction,
            ml_probability=probability,
            anomaly_score=0.0,
            network_score=0.0,
            fraud_ring_score=0.0,
            network_degree=0,
            connected_accounts=[],
        )

        base_decision = result["decision"]

        policy_decision = apply_policy(
            probability,
            base_decision,
        )

        print(
            f"{probability:<18.3f}"
            f"{result['risk_score']:<14.2f}"
            f"{base_decision:<16}"
            f"{policy_decision:<16}"
        )

    print("\n" + "=" * 78)
    print("POLICY TEST COMPLETE")
    print("=" * 78)
    print("No live pipeline or model files were modified.")


if __name__ == "__main__":
    main()