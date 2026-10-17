def anomaly_to_risk(
    score: float,
) -> float:

    return max(
        0.0,
        min(
            100.0,
            float(score) * 100.0,
        ),
    )