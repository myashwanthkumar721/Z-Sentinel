"""
Continuous real-time transaction stream runner.

Generates transactions continuously and sends them
through the complete Z-Sentinel processing pipeline.

Supports:
- Random real-time streaming
- Controlled hackathon demonstration mode
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime

from src.streaming.simulator import (
    TransactionStreamSimulator,
)

from src.streaming.processor import (
    TransactionProcessor,
)


class StreamRunner:
    """
    Continuously generate and process transactions.
    """

    # Controlled scenario for the hackathon demo.
    DEMO_SEQUENCE = [
        False,
        False,
        False,
        True,
        True,
        True,
        False,
    ]

    def __init__(
        self,
        interval_seconds: float = 2.0,
    ) -> None:

        self.interval_seconds = float(
            interval_seconds
        )

        self.simulator = (
            TransactionStreamSimulator()
        )

        self.processor = (
            TransactionProcessor()
        )

        self.running = False

    def process_one(
        self,
        suspicious: bool | None = None,
    ) -> dict:
        """
        Generate and process one transaction.
        """

        transaction = (
            self.simulator.generate_transaction(
                suspicious=suspicious
            )
        )

        result = self.processor.process(
            transaction
        )

        return result

    def _print_result(
        self,
        result: dict,
        sequence_label: str | None = None,
    ) -> None:
        """
        Print one processed transaction result.
        """

        transaction = result["transaction"]

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        label = ""

        if sequence_label:
            label = f"| {sequence_label:<10} "

        print(
            f"[{timestamp}] "
            f"{label}"
            f"{transaction['transaction_id']} "
            f"| "
            f"Amount: "
            f"{transaction['amount']:>8.2f} "
            f"| "
            f"ML: "
            f"{result['ml_probability'] * 100:>6.2f}% "
            f"| "
            f"Risk: "
            f"{result['risk_score']:>6.2f} "
            f"| "
            f"Decision: "
            f"{result['decision']}"
        )

    def run(
        self,
        max_transactions: int | None = None,
        demo: bool = False,
    ) -> None:
        """
        Run the transaction stream.

        Random mode:
            Transactions are generated using the
            simulator's normal random behavior.

        Demo mode:
            Transactions follow a controlled sequence:
            NORMAL → NORMAL → NORMAL →
            SUSPICIOUS → SUSPICIOUS → SUSPICIOUS →
            NORMAL
        """

        self.running = True

        processed = 0

        demo_sequence = list(
            self.DEMO_SEQUENCE
        )

        if demo and max_transactions is None:
            max_transactions = len(
                demo_sequence
            )

        print()
        print("=" * 78)
        print(
            "🛡️  Z-SENTINEL REAL-TIME STREAM"
        )
        print("=" * 78)

        if demo:

            print(
                "Mode: CONTROLLED HACKATHON DEMO"
            )

            print(
                "Scenario: "
                "NORMAL → NORMAL → NORMAL → "
                "SUSPICIOUS → SUSPICIOUS → "
                "SUSPICIOUS → NORMAL"
            )

        else:

            print(
                "Mode: RANDOM LIVE STREAM"
            )

        print(
            f"Interval: "
            f"{self.interval_seconds:.1f} seconds"
        )

        print(
            "Press Ctrl+C to stop."
        )

        print("=" * 78)
        print()

        try:

            while self.running:

                # ------------------------------------------------
                # Determine transaction behavior
                # ------------------------------------------------

                suspicious: bool | None = None
                sequence_label: str | None = None

                if demo:

                    if processed >= len(
                        demo_sequence
                    ):
                        break

                    suspicious = (
                        demo_sequence[processed]
                    )

                    sequence_label = (
                        "SUSPICIOUS"
                        if suspicious
                        else "NORMAL"
                    )

                # ------------------------------------------------
                # Process transaction
                # ------------------------------------------------

                result = self.process_one(
                    suspicious=suspicious
                )

                self._print_result(
                    result=result,
                    sequence_label=sequence_label,
                )

                processed += 1

                # ------------------------------------------------
                # Stop conditions
                # ------------------------------------------------

                if (
                    max_transactions is not None
                    and processed >= max_transactions
                ):
                    break

                if demo and (
                    processed
                    >= len(demo_sequence)
                ):
                    break

                time.sleep(
                    self.interval_seconds
                )

        except KeyboardInterrupt:

            print()
            print(
                "🛑 Stream stopped by user."
            )

        finally:

            self.running = False

            print()
            print(
                f"Transactions processed: "
                f"{processed}"
            )

            print("=" * 78)


def run_stream(
    interval_seconds: float = 2.0,
    max_transactions: int | None = None,
    demo: bool = False,
) -> None:
    """
    Convenience function for starting the stream.
    """

    runner = StreamRunner(
        interval_seconds=interval_seconds
    )

    runner.run(
        max_transactions=max_transactions,
        demo=demo,
    )


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Run the Z-Sentinel real-time "
            "transaction stream."
        )
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help=(
            "Run the controlled hackathon "
            "demonstration scenario."
        ),
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help=(
            "Seconds between transactions "
            "(default: 2.0)."
        ),
    )

    parser.add_argument(
        "--max-transactions",
        type=int,
        default=None,
        help=(
            "Maximum number of transactions "
            "to process."
        ),
    )

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()

    run_stream(
        interval_seconds=args.interval,
        max_transactions=args.max_transactions,
        demo=args.demo,
    )