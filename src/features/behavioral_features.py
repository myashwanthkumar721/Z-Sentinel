import pandas as pd


def add_behavioral_features(
    df: pd.DataFrame,
) -> pd.DataFrame:

    result = df.copy()

    result["young_account"] = (
        result["account_age_days"] < 30
    ).astype(int)

    result["young_device"] = (
        result["device_age_days"] < 30
    ).astype(int)

    result["failed_attempt_flag"] = (
        result["failed_attempts"] >= 3
    ).astype(int)

    return result