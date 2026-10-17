from pathlib import Path

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "amount",
    "hour",
    "transactions_last_1h",
    "amount_last_1h",
    "account_age_days",
    "device_age_days",
    "is_new_device",
    "is_international",
    "failed_attempts",
    "merchant_risk",
    "ip_risk",
    "network_degree",
]


def generate_transactions(
    n: int = 2000,
    seed: int = 42,
) -> pd.DataFrame:

    if n <= 0:
        raise ValueError("n must be greater than zero.")

    rng = np.random.default_rng(seed)

    amount = np.round(
        rng.lognormal(
            mean=4.2,
            sigma=1.0,
            size=n,
        ),
        2,
    )

    amount = np.clip(
        amount,
        1,
        50000,
    )

    hour = rng.integers(
        0,
        24,
        n,
    )

    transactions_last_1h = rng.poisson(
        2.0,
        n,
    )

    amount_last_1h = np.round(
        amount * rng.uniform(
            1.0,
            4.0,
            n,
        ),
        2,
    )

    account_age_days = rng.integers(
        10,
        2500,
        n,
    )

    device_age_days = rng.integers(
        1,
        1800,
        n,
    )

    is_new_device = (
        device_age_days < 30
    ).astype(int)

    is_international = rng.binomial(
        1,
        0.12,
        n,
    )

    failed_attempts = rng.poisson(
        0.4,
        n,
    )

    merchant_risk = np.round(
        rng.uniform(
            0,
            1,
            n,
        ),
        3,
    )

    ip_risk = np.round(
        rng.uniform(
            0,
            1,
            n,
        ),
        3,
    )

    network_degree = rng.integers(
        1,
        12,
        n,
    )

    risk_signal = (
        0.002 * amount
        + 0.10 * (
            (hour <= 4).astype(float)
        )
        + 0.08 * (
            (transactions_last_1h >= 7).astype(float)
        )
        + 0.08 * (
            (amount_last_1h > 1500).astype(float)
        )
        + 0.08 * is_new_device
        + 0.10 * is_international
        + 0.08 * (
            (failed_attempts >= 3).astype(float)
        )
        + 0.18 * merchant_risk
        + 0.16 * ip_risk
        + 0.08 * (
            (network_degree >= 8).astype(float)
        )
    )

    probability = 1 / (
        1 + np.exp(
            -(risk_signal * 5 - 2.5)
        )
    )

    is_fraud = rng.binomial(
        1,
        probability,
    )

    df = pd.DataFrame(
        {
            "transaction_id": [
                f"TX{100000 + i}"
                for i in range(n)
            ],
            "account_id": [
                f"A{rng.integers(1000, 1300)}"
                for _ in range(n)
            ],
            "device_id": [
                f"D{rng.integers(100, 450)}"
                for _ in range(n)
            ],
            "ip_address": [
                f"10.0.{rng.integers(1, 20)}."
                f"{rng.integers(1, 255)}"
                for _ in range(n)
            ],
            "merchant_id": [
                f"M{rng.integers(1, 100)}"
                for _ in range(n)
            ],
            "amount": amount,
            "hour": hour,
            "transactions_last_1h": transactions_last_1h,
            "amount_last_1h": amount_last_1h,
            "account_age_days": account_age_days,
            "device_age_days": device_age_days,
            "is_new_device": is_new_device,
            "is_international": is_international,
            "failed_attempts": failed_attempts,
            "merchant_risk": merchant_risk,
            "ip_risk": ip_risk,
            "network_degree": network_degree,
            "is_fraud": is_fraud,
        }
    )

    return df


def save_demo_data(
    path: str | Path,
    n: int = 2000,
    seed: int = 42,
) -> Path:

    output_path = Path(path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = generate_transactions(
        n=n,
        seed=seed,
    )

    df.to_csv(
        output_path,
        index=False,
    )

    return output_path