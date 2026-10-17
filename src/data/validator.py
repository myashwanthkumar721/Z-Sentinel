import pandas as pd


REQUIRED_COLUMNS = {
    "transaction_id",
    "account_id",
    "device_id",
    "ip_address",
    "merchant_id",
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
}


def validate_transactions(
    df: pd.DataFrame,
    require_target: bool = False,
) -> bool:

    if not isinstance(
        df,
        pd.DataFrame,
    ):
        raise TypeError(
            "Expected pandas DataFrame."
        )

    if df.empty:
        raise ValueError(
            "Transaction DataFrame is empty."
        )

    missing = (
        REQUIRED_COLUMNS
        - set(df.columns)
    )

    if require_target:
        if "is_fraud" not in df.columns:
            missing.add("is_fraud")

    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(sorted(missing))
        )

    if df["transaction_id"].isna().any():
        raise ValueError(
            "transaction_id contains missing values."
        )

    if df["transaction_id"].duplicated().any():
        raise ValueError(
            "Duplicate transaction IDs found."
        )

    if (df["amount"] < 0).any():
        raise ValueError(
            "Negative transaction amount found."
        )

    if require_target:
        if not df["is_fraud"].isin([0, 1]).all():
            raise ValueError(
                "is_fraud must contain only 0 and 1."
            )

    return True