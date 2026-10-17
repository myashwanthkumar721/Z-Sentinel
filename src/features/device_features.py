import pandas as pd


def add_device_features(
    df: pd.DataFrame,
) -> pd.DataFrame:

    result = df.copy()

    result["device_risk"] = (
        0.65
        * result["is_new_device"].clip(0, 1)
        + 0.35
        * (
            result["device_age_days"] < 14
        ).astype(int)
    ).clip(0, 1)

    return result