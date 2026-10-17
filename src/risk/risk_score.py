from config.thresholds import (
    ANOMALY_WEIGHT,
    DEVICE_WEIGHT,
    ML_WEIGHT,
    NETWORK_WEIGHT,
    VELOCITY_WEIGHT,
)

from src.utils.helpers import clamp


def calculate_risk_score(
    ml_probability: float,
    anomaly_score: float,
    network_score: float,
    velocity_score: float,
    device_score: float,
) -> float:

    score = 100.0 * (
        ML_WEIGHT * ml_probability
        + ANOMALY_WEIGHT * anomaly_score
        + NETWORK_WEIGHT * network_score
        + VELOCITY_WEIGHT * velocity_score
        + DEVICE_WEIGHT * device_score
    )

    return round(
        clamp(score),
        2,
    )