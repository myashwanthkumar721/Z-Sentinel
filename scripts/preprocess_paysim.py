"""
Z-Sentinel - PaySim preprocessing pipeline.

Phase 12.2-A
------------
Converts the raw PaySim transaction dataset into a compact,
fraud-detection-ready feature dataset.

Important:
The transaction type encoding uses a fixed mapping across every
chunk so that the same transaction type always receives the same
numeric value.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "PS_20174392719_1491204439457_log.csv"
)

PROCESSED_DIR = BASE_DIR / "data" / "processed"

OUTPUT_FILE = PROCESSED_DIR / "paysim_features.csv"
SUMMARY_FILE = PROCESSED_DIR / "paysim_summary.json"

CHUNK_SIZE = 250_000


# -------------------------------------------------------------------
# Fixed PaySim transaction-type encoding
# -------------------------------------------------------------------

TRANSACTION_TYPE_MAPPING = {
    "CASH_IN": 0,
    "CASH_OUT": 1,
    "DEBIT": 2,
    "PAYMENT": 3,
    "TRANSFER": 4,
}


REQUIRED_COLUMNS = [
    "step",
    "type",
    "amount",
    "nameOrig",
    "oldbalanceOrg",
    "newbalanceOrig",
    "nameDest",
    "oldbalanceDest",
    "newbalanceDest",
    "isFraud",
    "isFlaggedFraud",
]


def validate_input_columns(columns: list[str]) -> None:
    """Validate that the raw PaySim file contains expected columns."""

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in columns
    ]

    if missing:
        raise ValueError(
            "PaySim dataset is missing required columns: "
            + ", ".join(missing)
        )


def encode_transaction_type(series: pd.Series) -> pd.Series:
    """
    Encode PaySim transaction types using a fixed global mapping.

    This prevents different chunks from receiving different category
    codes for the same transaction type.
    """

    normalized = (
        series
        .astype(str)
        .str.strip()
        .str.upper()
    )

    unknown_types = sorted(
        set(normalized.unique())
        - set(TRANSACTION_TYPE_MAPPING.keys())
    )

    if unknown_types:
        raise ValueError(
            "Unknown PaySim transaction type(s): "
            + ", ".join(unknown_types)
        )

    return normalized.map(TRANSACTION_TYPE_MAPPING).astype("int8")


def build_features(chunk: pd.DataFrame) -> pd.DataFrame:
    """Create fraud-detection features from a PaySim chunk."""

    df = chunk.copy()

    # ---------------------------------------------------------------
    # Basic transaction features
    # ---------------------------------------------------------------

    df["amount"] = (
        pd.to_numeric(
            df["amount"],
            errors="coerce",
        )
        .fillna(0.0)
    )

    df["transaction_type"] = encode_transaction_type(
        df["type"]
    )

    # ---------------------------------------------------------------
    # Sender balance features
    # ---------------------------------------------------------------

    df["sender_balance_before"] = (
        pd.to_numeric(
            df["oldbalanceOrg"],
            errors="coerce",
        )
        .fillna(0.0)
    )

    df["sender_balance_after"] = (
        pd.to_numeric(
            df["newbalanceOrig"],
            errors="coerce",
        )
        .fillna(0.0)
    )

    df["sender_balance_change"] = (
        df["sender_balance_before"]
        - df["sender_balance_after"]
    )

    df["sender_balance_error"] = (
        df["sender_balance_after"]
        - (
            df["sender_balance_before"]
            - df["amount"]
        )
    )

    df["sender_zero_balance_after"] = (
        (
            df["sender_balance_after"] <= 0
        )
        .astype("int8")
    )

    # ---------------------------------------------------------------
    # Receiver balance features
    # ---------------------------------------------------------------

    df["receiver_balance_before"] = (
        pd.to_numeric(
            df["oldbalanceDest"],
            errors="coerce",
        )
        .fillna(0.0)
    )

    df["receiver_balance_after"] = (
        pd.to_numeric(
            df["newbalanceDest"],
            errors="coerce",
        )
        .fillna(0.0)
    )

    df["receiver_balance_change"] = (
        df["receiver_balance_after"]
        - df["receiver_balance_before"]
    )

    df["receiver_balance_error"] = (
        df["receiver_balance_after"]
        - (
            df["receiver_balance_before"]
            + df["amount"]
        )
    )

    df["receiver_zero_balance_before"] = (
        (
            df["receiver_balance_before"] <= 0
        )
        .astype("int8")
    )

    # ---------------------------------------------------------------
    # Amount / balance relationship features
    # ---------------------------------------------------------------

    df["amount_to_sender_balance_ratio"] = (
        df["amount"]
        / df["sender_balance_before"]
        .replace(0, np.nan)
    )

    df["amount_to_sender_balance_ratio"] = (
        df["amount_to_sender_balance_ratio"]
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .fillna(0.0)
    )

    df["amount_exceeds_sender_balance"] = (
        df["amount"]
        > df["sender_balance_before"]
    ).astype("int8")

    # ---------------------------------------------------------------
    # Time features
    # ---------------------------------------------------------------

    df["step"] = (
        pd.to_numeric(
            df["step"],
            errors="coerce",
        )
        .fillna(0)
        .astype("int32")
    )

    df["hour_proxy"] = (
        df["step"] % 24
    )

    df["day_proxy"] = (
        df["step"] // 24
    )

    # ---------------------------------------------------------------
    # Fraud flag
    # ---------------------------------------------------------------

    df["is_flagged_fraud"] = (
        pd.to_numeric(
            df["isFlaggedFraud"],
            errors="coerce",
        )
        .fillna(0)
        .astype("int8")
    )

    # ---------------------------------------------------------------
    # Account-type features
    # ---------------------------------------------------------------

    df["origin_is_customer"] = (
        df["nameOrig"]
        .astype(str)
        .str.startswith("C")
    ).astype("int8")

    df["destination_is_customer"] = (
        df["nameDest"]
        .astype(str)
        .str.startswith("C")
    ).astype("int8")

    df["same_account_type"] = (
        df["origin_is_customer"]
        == df["destination_is_customer"]
    ).astype("int8")

    # ---------------------------------------------------------------
    # Target
    # ---------------------------------------------------------------

    df["is_fraud"] = (
        pd.to_numeric(
            df["isFraud"],
            errors="coerce",
        )
        .fillna(0)
        .astype("int8")
    )

    # ---------------------------------------------------------------
    # Final feature set
    # ---------------------------------------------------------------

    feature_columns = [
        "step",
        "transaction_type",
        "amount",
        "sender_balance_before",
        "sender_balance_after",
        "sender_balance_change",
        "sender_balance_error",
        "sender_zero_balance_after",
        "receiver_balance_before",
        "receiver_balance_after",
        "receiver_balance_change",
        "receiver_balance_error",
        "receiver_zero_balance_before",
        "amount_to_sender_balance_ratio",
        "amount_exceeds_sender_balance",
        "hour_proxy",
        "day_proxy",
        "is_flagged_fraud",
        "origin_is_customer",
        "destination_is_customer",
        "same_account_type",
        "is_fraud",
    ]

    result = df[feature_columns].copy()

    result.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True,
    )

    numeric_columns = (
        result
        .select_dtypes(include=[np.number])
        .columns
    )

    result[numeric_columns] = (
        result[numeric_columns]
        .fillna(0)
    )

    return result


def process_paysim() -> dict:
    """Process the complete PaySim dataset in chunks."""

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"PaySim dataset not found:\n{RAW_FILE}"
        )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    if SUMMARY_FILE.exists():
        SUMMARY_FILE.unlink()

    total_rows = 0
    fraud_rows = 0
    normal_rows = 0

    first_write = True

    print("=" * 70)
    print("Z-SENTINEL - PAYSIM PREPROCESSING")
    print("=" * 70)

    print(f"Input : {RAW_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Chunk : {CHUNK_SIZE:,} rows")
    print()

    reader = pd.read_csv(
        RAW_FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )

    for chunk_number, chunk in enumerate(
        reader,
        start=1,
    ):
        validate_input_columns(
            chunk.columns.tolist()
        )

        processed = build_features(
            chunk
        )

        rows = len(processed)

        fraud = int(
            processed["is_fraud"].sum()
        )

        normal = rows - fraud

        total_rows += rows
        fraud_rows += fraud
        normal_rows += normal

        processed.to_csv(
            OUTPUT_FILE,
            mode=(
                "w"
                if first_write
                else "a"
            ),
            header=first_write,
            index=False,
        )

        first_write = False

        fraud_rate = (
            (fraud_rows / total_rows)
            * 100
            if total_rows
            else 0.0
        )

        print(
            f"Chunk {chunk_number:02d} | "
            f"rows={total_rows:,} | "
            f"fraud={fraud_rows:,} | "
            f"fraud_rate={fraud_rate:.4f}%"
        )

    summary = {
        "dataset": "PaySim",
        "source_file": str(RAW_FILE),
        "processed_file": str(
            OUTPUT_FILE
        ),
        "total_rows": total_rows,
        "fraud_rows": fraud_rows,
        "normal_rows": normal_rows,
        "fraud_rate_percent": (
            (fraud_rows / total_rows)
            * 100
            if total_rows
            else 0.0
        ),
        "chunk_size": CHUNK_SIZE,
        "feature_count": 21,
        "target_column": "is_fraud",
        "transaction_type_mapping": (
            TRANSACTION_TYPE_MAPPING
        ),
        "feature_columns": [
            "step",
            "transaction_type",
            "amount",
            "sender_balance_before",
            "sender_balance_after",
            "sender_balance_change",
            "sender_balance_error",
            "sender_zero_balance_after",
            "receiver_balance_before",
            "receiver_balance_after",
            "receiver_balance_change",
            "receiver_balance_error",
            "receiver_zero_balance_before",
            "amount_to_sender_balance_ratio",
            "amount_exceeds_sender_balance",
            "hour_proxy",
            "day_proxy",
            "is_flagged_fraud",
            "origin_is_customer",
            "destination_is_customer",
            "same_account_type",
        ],
    }

    with SUMMARY_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=2,
        )

    print()
    print("=" * 70)
    print("PREPROCESSING COMPLETE")
    print("=" * 70)

    print(
        f"Total rows : {total_rows:,}"
    )

    print(
        f"Fraud rows : {fraud_rows:,}"
    )

    print(
        f"Normal rows: {normal_rows:,}"
    )

    print(
        f"Fraud rate : "
        f"{summary['fraud_rate_percent']:.4f}%"
    )

    print()
    print(
        f"Features   : {OUTPUT_FILE}"
    )

    print(
        f"Summary    : {SUMMARY_FILE}"
    )

    print()
    print(
        "Transaction type mapping:"
    )

    for name, code in (
        TRANSACTION_TYPE_MAPPING.items()
    ):
        print(
            f"  {name:<10} -> {code}"
        )

    return summary


if __name__ == "__main__":
    process_paysim()