import pandas as pd


NUMERIC_COLUMNS = [
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
    "is_fraud",
]


def clean_transactions(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        raise ValueError(
            "Transaction DataFrame is empty."
        )

    result = df.copy()

    if "transaction_id" in result.columns:
        result = result.drop_duplicates(
            subset=["transaction_id"]
        )
    else:
        result = result.drop_duplicates()

    for column in NUMERIC_COLUMNS:

        if column not in result.columns:
            continue

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).fillna(0)

    if "amount" in result.columns:
        result["amount"] = result["amount"].clip(
            lower=0
        )

    if "hour" in result.columns:
        result["hour"] = result["hour"].clip(
            lower=0,
            upper=23,
        )

    for column in [
        "is_new_device",
        "is_international",
        "is_fraud",
    ]:

        if column in result.columns:
            result[column] = (
                result[column]
                .astype(int)
                .clip(0, 1)
            )

    return result.reset_index(
        drop=True
    )