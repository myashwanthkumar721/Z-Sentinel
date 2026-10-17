import pandas as pd


def add_velocity_features(
    df: pd.DataFrame,
) -> pd.DataFrame:

    result = df.copy()

    transaction_velocity = (
        result["transactions_last_1h"]
        .clip(0, 20)
        / 20.0
    )

    amount_velocity = (
        result["amount_last_1h"]
        .clip(0, 5000)
        / 5000.0
    )

    result["velocity_score"] = (
        transaction_velocity
        + amount_velocity
    ) / 2.0

    return result