import numpy as np
import pandas as pd


def build_transaction_features(
    df: pd.DataFrame,
) -> pd.DataFrame:

    result = df.copy()

    result["amount_log"] = np.log1p(
        result["amount"].clip(lower=0)
    )

    result["is_night"] = (
        result["hour"].isin(
            [0, 1, 2, 3, 4, 5]
        )
    ).astype(int)

    result["high_velocity"] = (
        result["transactions_last_1h"] >= 7
    ).astype(int)

    result["high_hourly_amount"] = (
        result["amount_last_1h"] >= 1500
    ).astype(int)

    return result