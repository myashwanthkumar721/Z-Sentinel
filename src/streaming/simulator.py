"""
Real-time transaction stream simulator for Z-Sentinel.

Generates realistic transaction events that can be processed
one at a time by the fraud detection pipeline.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime


class TransactionStreamSimulator:
    """
    Generate simulated financial transactions continuously.

    The simulator deliberately creates both normal and
    suspicious transaction patterns for demonstration.
    """

    def __init__(
        self,
        account_pool_size: int = 20,
        device_pool_size: int = 30,
        merchant_pool_size: int = 20,
    ) -> None:

        self.accounts = [
            f"ACC-{uuid.uuid4().hex[:8].upper()}"
            for _ in range(account_pool_size)
        ]

        self.devices = [
            f"DEV-{uuid.uuid4().hex[:8].upper()}"
            for _ in range(device_pool_size)
        ]

        self.merchants = [
            f"MERCHANT-{uuid.uuid4().hex[:8].upper()}"
            for _ in range(merchant_pool_size)
        ]

        self.transaction_count = 0

    def _generate_ip(self) -> str:
        """
        Generate a simulated IP address.
        """

        return (
            f"10."
            f"{random.randint(1, 254)}."
            f"{random.randint(1, 254)}."
            f"{random.randint(1, 254)}"
        )

    def generate_transaction(
        self,
        suspicious: bool | None = None,
    ) -> dict:
        """
        Generate one transaction event.

        suspicious:
            True  -> deliberately risky transaction
            False -> deliberately normal transaction
            None  -> randomly selected behavior
        """

        self.transaction_count += 1

        if suspicious is None:

            suspicious = (
                random.random() < 0.15
            )

        account_id = random.choice(
            self.accounts
        )

        # ----------------------------------------------------
        # Normal transaction
        # ----------------------------------------------------

        if not suspicious:

            amount = round(
                random.uniform(
                    20,
                    500,
                ),
                2,
            )

            velocity = random.randint(
                1,
                5,
            )

            failed_attempts = random.randint(
                0,
                1,
            )

            new_device = (
                random.random() < 0.05
            )

            international = (
                random.random() < 0.05
            )

            merchant_risk = round(
                random.uniform(
                    0.05,
                    0.30,
                ),
                2,
            )

            ip_risk = round(
                random.uniform(
                    0.05,
                    0.25,
                ),
                2,
            )

        # ----------------------------------------------------
        # Suspicious transaction
        # ----------------------------------------------------

        else:

            amount = round(
                random.uniform(
                    1500,
                    10000,
                ),
                2,
            )

            velocity = random.randint(
                10,
                40,
            )

            failed_attempts = random.randint(
                3,
                10,
            )

            new_device = True

            international = True

            merchant_risk = round(
                random.uniform(
                    0.70,
                    1.00,
                ),
                2,
            )

            ip_risk = round(
                random.uniform(
                    0.70,
                    1.00,
                ),
                2,
            )

        device_id = random.choice(
            self.devices
        )

        merchant_id = random.choice(
            self.merchants
        )

        transaction = {

            "transaction_id":
                "TX-"
                + datetime.now().strftime(
                    "%Y%m%d%H%M%S"
                )
                + "-"
                + uuid.uuid4().hex[:8].upper(),

            "account_id":
                account_id,

            "device_id":
                device_id,

            "ip_address":
                self._generate_ip(),

            "merchant_id":
                merchant_id,

            "amount":
                amount,

            "hour":
                datetime.now().hour,

            "transactions_last_1h":
                velocity,

            "amount_last_1h":
                round(
                    amount
                    * max(
                        1,
                        velocity,
                    ),
                    2,
                ),

            "account_age_days":
                random.randint(
                    30,
                    2000,
                ),

            "device_age_days":
                (
                    random.randint(
                        1,
                        10,
                    )
                    if new_device
                    else random.randint(
                        30,
                        1000,
                    )
                ),

            "is_new_device":
                int(new_device),

            "is_international":
                int(international),

            "failed_attempts":
                failed_attempts,

            "merchant_risk":
                merchant_risk,

            "ip_risk":
                ip_risk,

            "network_degree":
                3,
        }

        return transaction


def generate_stream(
    count: int = 10,
) -> list[dict]:
    """
    Generate a finite list of simulated transactions.
    """

    simulator = TransactionStreamSimulator()

    return [
        simulator.generate_transaction()
        for _ in range(count)
    ]