"""
Runs a three-account coordinated-fraud scenario through the
real Z-Sentinel TransactionProcessor.

The existing network history is backed up and restored after
the demonstration so the demo does not permanently modify
the project's normal network history.
"""

from __future__ import annotations

import pandas as pd

from src.network.fraud_rings import (
    detect_fraud_rings,
)

from src.network.graph_builder import (
    build_transaction_graph,
)

from src.network.history import (
    HISTORY_FILE,
    clear_network_history,
    load_network_history,
)

from src.streaming.processor import (
    TransactionProcessor,
)


# ============================================================
# CONTROLLED FRAUD-RING SCENARIO
# ============================================================

DEMO_TRANSACTIONS = [
    {
        "transaction_id": "RING-DEMO-TX-001",
        "account_id": "RING-DEMO-01",
        "device_id": "RING-DEVICE-01",
        "ip_address": "10.99.0.1",
        "merchant_id": "RING-MERCHANT-01",
        "amount": 2450.00,
        "velocity": 12,
        "failed_attempts": 3,
        "new_device": True,
        "international": True,
        "merchant_risk": 0.85,
        "ip_risk": 0.80,
    },
    {
        "transaction_id": "RING-DEMO-TX-002",
        "account_id": "RING-DEMO-02",
        "device_id": "RING-DEVICE-01",
        "ip_address": "10.99.0.1",
        "merchant_id": "RING-MERCHANT-01",
        "amount": 3200.00,
        "velocity": 15,
        "failed_attempts": 4,
        "new_device": True,
        "international": True,
        "merchant_risk": 0.90,
        "ip_risk": 0.85,
    },
    {
        "transaction_id": "RING-DEMO-TX-003",
        "account_id": "RING-DEMO-03",
        "device_id": "RING-DEVICE-01",
        "ip_address": "10.99.0.1",
        "merchant_id": "RING-MERCHANT-01",
        "amount": 4100.00,
        "velocity": 18,
        "failed_attempts": 5,
        "new_device": True,
        "international": True,
        "merchant_risk": 0.95,
        "ip_risk": 0.90,
    },
]


# ============================================================
# HISTORY BACKUP / RESTORE
# ============================================================

def backup_history() -> bytes | None:
    """
    Save the exact current network-history file contents.
    """

    if not HISTORY_FILE.exists():
        return None

    return HISTORY_FILE.read_bytes()


def restore_history(
    original_data: bytes | None,
) -> None:
    """
    Restore the exact network-history state that existed
    before the demonstration.
    """

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


# ============================================================
# RESULT DISPLAY
# ============================================================

def print_result(
    index: int,
    result: dict,
) -> None:
    """
    Print the investigation result for one transaction.
    """

    transaction = result["transaction"]

    print()
    print("=" * 72)
    print(
        f"TRANSACTION {index}: "
        f"{transaction['transaction_id']}"
    )
    print("=" * 72)

    print(
        f"Account            : "
        f"{transaction['account_id']}"
    )

    print(
        f"Amount             : "
        f"{transaction['amount']:.2f}"
    )

    print(
        f"ML probability     : "
        f"{result['ml_probability'] * 100:.2f}%"
    )

    print(
        f"Network degree     : "
        f"{result['network_degree']}"
    )

    print(
        f"Fraud-ring score   : "
        f"{result['fraud_ring_score']:.4f}"
    )

    print(
        f"Ring detected      : "
        f"{result['fraud_ring_detected']}"
    )

    connected_accounts = result[
        "connected_accounts"
    ]

    connected_ids = [
        item["account_id"]
        for item in connected_accounts
    ]

    print(
        f"Connected accounts : "
        f"{connected_ids}"
    )

    print(
        f"Risk score         : "
        f"{result['risk_score']:.2f}"
    )

    print(
        f"Decision           : "
        f"{result['decision']}"
    )


# ============================================================
# MAIN DEMONSTRATION
# ============================================================

def main() -> None:
    """
    Run the complete controlled fraud-ring demonstration.
    """

    print()
    print("=" * 72)
    print("Z-SENTINEL — PHASE 14 FRAUD-RING SHOWCASE")
    print("=" * 72)

    print()
    print("Scenario:")
    print(
        "Three accounts share the same device, IP address "
        "and merchant."
    )

    print()
    print("Accounts:")
    print("  RING-DEMO-01")
    print("  RING-DEMO-02")
    print("  RING-DEMO-03")

    # --------------------------------------------------------
    # Preserve the user's original network history.
    # --------------------------------------------------------

    original_history = backup_history()

    try:

        # ----------------------------------------------------
        # Start the demonstration from a clean network.
        # ----------------------------------------------------

        clear_network_history()

        processor = TransactionProcessor(
            model_name="existing"
        )

        results = []

        # ----------------------------------------------------
        # Process the three transactions sequentially.
        #
        # save_history=True is intentional.
        #
        # This allows each later transaction to see the
        # infrastructure relationships created by previous
        # transactions.
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

            print_result(
                index,
                result,
            )

        # ----------------------------------------------------
        # Build the final graph from the demonstration history.
        # ----------------------------------------------------

        history = load_network_history()

        graph = build_transaction_graph(
            history[
                [
                    "account_id",
                    "device_id",
                    "ip_address",
                    "merchant_id",
                ]
            ]
        )

        # ----------------------------------------------------
        # Independently detect complete fraud rings.
        # ----------------------------------------------------

        rings = detect_fraud_rings(
            graph,
            minimum_accounts=3,
        )

        print()
        print("=" * 72)
        print("FINAL FRAUD-RING VERIFICATION")
        print("=" * 72)

        print(
            f"Transactions processed : "
            f"{len(results)}"
        )

        print(
            f"Detected rings         : "
            f"{len(rings)}"
        )

        if rings:

            ring = rings[0]

            print(
                f"Ring account count     : "
                f"{ring['account_count']}"
            )

            print(
                f"Ring accounts          : "
                f"{ring['accounts']}"
            )

            print(
                f"Network density        : "
                f"{ring['network_density']:.4f}"
            )

        else:

            print(
                "No three-account fraud ring detected."
            )

        # ====================================================
        # ACCEPTANCE CHECKS
        # ====================================================

        # Exactly three demonstration transactions.
        assert len(results) == 3

        # First account has no previous connected account.
        assert (
            results[0][
                "fraud_ring_detected"
            ]
            is False
        )

        assert (
            len(
                results[0][
                    "connected_accounts"
                ]
            )
            == 0
        )

        # Second account sees exactly one previous account.
        # A complete ring requires at least two connected
        # accounts, so detection remains False.
        assert (
            results[1][
                "fraud_ring_detected"
            ]
            is False
        )

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

        # Third account sees both previous accounts.
        assert (
            results[2][
                "fraud_ring_detected"
            ]
            is True
        )

        assert (
            len(
                results[2][
                    "connected_accounts"
                ]
            )
            == 2
        )

        assert (
            results[2][
                "fraud_ring_score"
            ]
            > 0.0
        )

        # Independent final graph verification.
        assert len(rings) == 1

        assert (
            rings[0][
                "account_count"
            ]
            == 3
        )

        assert set(
            rings[0]["accounts"]
        ) == {
            "RING-DEMO-01",
            "RING-DEMO-02",
            "RING-DEMO-03",
        }

        assert (
            rings[0][
                "network_density"
            ]
            > 0.0
        )

        # ----------------------------------------------------
        # All acceptance checks passed.
        # ----------------------------------------------------

        print()
        print("=" * 72)
        print("ACCEPTANCE CHECKS: PASS")
        print("=" * 72)

        print(
            "✓ Sequential coordinated activity detected"
        )

        print(
            "✓ Shared device relationship detected"
        )

        print(
            "✓ Shared IP relationship detected"
        )

        print(
            "✓ Shared merchant relationship detected"
        )

        print(
            "✓ Connected accounts identified"
        )

        print(
            "✓ Fraud-ring score generated"
        )

        print(
            "✓ Three-account ring independently verified"
        )

    finally:

        # ----------------------------------------------------
        # Always restore the original network history.
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
    print("ACCEPTANCE CHECKS: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()