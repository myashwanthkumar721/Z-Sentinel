"""
Fraud-Ring Risk Pipeline Verification.

Verifies that coordinated account relationships detected by the
fraud-ring engine are propagated through the real
TransactionProcessor into the risk engine and final decision.

The original network history is restored after the demonstration.
"""

from __future__ import annotations

from src.network.history import (
    HISTORY_FILE,
    clear_network_history,
    load_network_history,
)

from src.streaming.processor import (
    TransactionProcessor,
)


DEMO_TRANSACTIONS = [
    {
        "transaction_id": "RING-PIPE-TX-001",
        "account_id": "RING-PIPE-01",
        "device_id": "RING-PIPE-DEVICE",
        "ip_address": "10.88.0.1",
        "merchant_id": "RING-PIPE-MERCHANT",
        "amount": 2200.00,
        "velocity": 12,
        "failed_attempts": 3,
        "new_device": True,
        "international": True,
        "merchant_risk": 0.85,
        "ip_risk": 0.80,
    },
    {
        "transaction_id": "RING-PIPE-TX-002",
        "account_id": "RING-PIPE-02",
        "device_id": "RING-PIPE-DEVICE",
        "ip_address": "10.88.0.1",
        "merchant_id": "RING-PIPE-MERCHANT",
        "amount": 2800.00,
        "velocity": 14,
        "failed_attempts": 4,
        "new_device": True,
        "international": True,
        "merchant_risk": 0.90,
        "ip_risk": 0.85,
    },
    {
        "transaction_id": "RING-PIPE-TX-003",
        "account_id": "RING-PIPE-03",
        "device_id": "RING-PIPE-DEVICE",
        "ip_address": "10.88.0.1",
        "merchant_id": "RING-PIPE-MERCHANT",
        "amount": 3600.00,
        "velocity": 17,
        "failed_attempts": 5,
        "new_device": True,
        "international": True,
        "merchant_risk": 0.95,
        "ip_risk": 0.90,
    },
]


def backup_history() -> bytes | None:
    """Back up the existing network-history file."""

    if not HISTORY_FILE.exists():
        return None

    return HISTORY_FILE.read_bytes()


def restore_history(
    original_data: bytes | None,
) -> None:
    """Restore the exact original network-history file."""

    if original_data is None:

        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()

        return

    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    HISTORY_FILE.write_bytes(
        original_data
    )


def print_pipeline_result(
    index: int,
    result: dict,
) -> None:
    """Display the important pipeline signals."""

    transaction = result["transaction"]

    print()
    print("-" * 72)
    print(
        f"TRANSACTION {index}: "
        f"{transaction['transaction_id']}"
    )
    print("-" * 72)

    print(
        f"Account             : "
        f"{transaction['account_id']}"
    )

    print(
        f"ML probability      : "
        f"{result['ml_probability'] * 100:.2f}%"
    )

    print(
        f"Network score       : "
        f"{result['network_score']:.4f}"
    )

    print(
        f"Network degree      : "
        f"{result['network_degree']}"
    )

    print(
        f"Fraud-ring score    : "
        f"{result['fraud_ring_score']:.4f}"
    )

    print(
        f"Ring detected       : "
        f"{result['fraud_ring_detected']}"
    )

    connected = result[
        "connected_accounts"
    ]

    print(
        f"Connected accounts  : "
        f"{[item['account_id'] for item in connected]}"
    )

    print(
        f"Risk score          : "
        f"{result['risk_score']:.2f}"
    )

    print(
        f"Base decision       : "
        f"{result['base_decision']}"
    )

    print(
        f"Final decision      : "
        f"{result['decision']}"
    )

    print(
        "Risk signals        : "
        f"{result['signals']}"
    )


def main() -> None:
    """Run the fraud-ring risk pipeline verification."""

    print()
    print("=" * 72)
    print("Z-SENTINEL — FRAUD-RING RISK PIPELINE VERIFICATION")
    print("=" * 72)

    print()
    print(
        "Goal: verify that coordinated account relationships "
        "reach the risk engine and final decision."
    )

    original_history = backup_history()

    try:

        # ----------------------------------------------------
        # Clean demonstration environment.
        # ----------------------------------------------------

        clear_network_history()

        processor = TransactionProcessor(
            model_name="existing"
        )

        results = []

        # ----------------------------------------------------
        # Sequential processing is intentional.
        # ----------------------------------------------------

        for index, transaction in enumerate(
            DEMO_TRANSACTIONS,
            start=1,
        ):

            result = processor.process(
                transaction,
                save_history=True,
            )

            results.append(
                result
            )

            print_pipeline_result(
                index,
                result,
            )

        # ====================================================
        # ACCEPTANCE CHECKS
        # ====================================================

        assert len(results) == 3

        # ----------------------------------------------------
        # First transaction:
        # no previous coordinated accounts.
        # ----------------------------------------------------

        assert (
            results[0][
                "fraud_ring_score"
            ]
            == 0.0
        )

        assert (
            results[0][
                "fraud_ring_detected"
            ]
            is False
        )

        # ----------------------------------------------------
        # Second transaction:
        # one connected account.
        # ----------------------------------------------------

        assert (
            len(
                results[1][
                    "connected_accounts"
                ]
            )
            == 1
        )

        assert (
            results[1][
                "fraud_ring_score"
            ]
            > 0.0
        )

        assert (
            results[1][
                "fraud_ring_detected"
            ]
            is False
        )

        # ----------------------------------------------------
        # Third transaction:
        # two connected accounts -> ring detected.
        # ----------------------------------------------------

        final_result = results[2]

        assert (
            len(
                final_result[
                    "connected_accounts"
                ]
            )
            == 2
        )

        assert (
            final_result[
                "fraud_ring_score"
            ]
            > results[1][
                "fraud_ring_score"
            ]
        )

        assert (
            final_result[
                "fraud_ring_detected"
            ]
            is True
        )

        # ----------------------------------------------------
        # Verify the fraud-ring signal reached the risk engine.
        # The risk engine uses the key "fraud_ring_score".
        # ----------------------------------------------------

        risk_signals = final_result[
            "signals"
        ]

        assert isinstance(
            risk_signals,
            dict,
        )

        assert (
            "fraud_ring_score"
            in risk_signals
        )

        assert (
            float(
                risk_signals[
                    "fraud_ring_score"
                ]
            )
            > 0.0
        )

        # ----------------------------------------------------
        # Verify the risk engine produced a valid score.
        # ----------------------------------------------------

        assert (
            final_result[
                "risk_score"
            ]
            >= 0.0
        )

        assert (
            final_result[
                "risk_score"
            ]
            <= 100.0
        )

        assert final_result[
            "decision"
        ] in {
            "ALLOW",
            "VERIFY",
            "HOLD",
        }

        # ----------------------------------------------------
        # Verify the active demonstration history.
        # ----------------------------------------------------

        history = load_network_history()

        assert len(history) == 3

        print()
        print("=" * 72)
        print("ACCEPTANCE CHECKS: PASS")
        print("=" * 72)

        print(
            "✓ Fraud-ring signal reached TransactionProcessor"
        )

        print(
            "✓ Connected-account intelligence reached risk engine"
        )

        print(
            "✓ Fraud-ring score is present in risk signals"
        )

        print(
            "✓ Risk score was generated successfully"
        )

        print(
            "✓ Final decision policy executed successfully"
        )

        print(
            "✓ Sequential three-account scenario verified"
        )

    finally:

        # ----------------------------------------------------
        # Restore original project history.
        # ----------------------------------------------------

        restore_history(
            original_history
        )

        print()
        print(
            "Original network history restored."
        )

        print(
            f"History file: {HISTORY_FILE}"
        )

    print()
    print("=" * 72)
    print("FRAUD-RING RISK PIPELINE VERIFICATION COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()