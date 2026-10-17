"""
Risk thresholds and signal weights for Z-Sentinel.

The weights represent the relative contribution of each
fraud-intelligence signal to the final risk score.
"""

# ============================================================
# DECISION THRESHOLDS
# ============================================================

ALLOW_MAX = 39.0
VERIFY_MAX = 69.0
HOLD_MIN = 70.0


# ============================================================
# RISK SIGNAL WEIGHTS
# ============================================================

ML_WEIGHT = 0.35
ANOMALY_WEIGHT = 0.15
NETWORK_WEIGHT = 0.20
FRAUD_RING_WEIGHT = 0.15
VELOCITY_WEIGHT = 0.10
DEVICE_WEIGHT = 0.05


def validate_thresholds() -> None:
    """
    Validate decision thresholds and risk weights.
    """

    assert 0 <= ALLOW_MAX < VERIFY_MAX < 100

    assert HOLD_MIN == VERIFY_MAX + 1

    total_weight = (
        ML_WEIGHT
        + ANOMALY_WEIGHT
        + NETWORK_WEIGHT
        + FRAUD_RING_WEIGHT
        + VELOCITY_WEIGHT
        + DEVICE_WEIGHT
    )

    assert abs(
        total_weight - 1.0
    ) < 1e-9


validate_thresholds()