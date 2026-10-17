"""
PaySim fraud-model predictor for Z-Sentinel.

This module loads the separately trained PaySim model and converts
a PaySim-style transaction into the exact feature structure expected
by that model.

The existing demo fraud model is not modified.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_DIR = BASE_DIR / "models"

MODEL_FILE = MODEL_DIR / "paysim_fraud_model.pkl"

FEATURE_FILE = (
    MODEL_DIR
    / "paysim_feature_columns.json"
)


# -------------------------------------------------------------------
# PaySim transaction-type mapping
# -------------------------------------------------------------------

TRANSACTION_TYPE_MAPPING = {
    "CASH_IN": 0,
    "CASH_OUT": 1,
    "DEBIT": 2,
    "PAYMENT": 3,
    "TRANSFER": 4,
}


# -------------------------------------------------------------------
# Model loading
# -------------------------------------------------------------------

_model = None
_feature_columns: list[str] | None = None


def load_paysim_model():
    """
    Load the PaySim fraud model once and reuse it.
    """

    global _model

    if _model is None:

        if not MODEL_FILE.exists():
            raise FileNotFoundError(
                f"PaySim model not found:\n{MODEL_FILE}"
            )

        _model = joblib.load(
            MODEL_FILE
        )

    return _model


def load_feature_columns() -> list[str]:
    """
    Load the exact feature order used during training.
    """

    global _feature_columns

    if _feature_columns is None:

        if not FEATURE_FILE.exists():
            raise FileNotFoundError(
                f"PaySim feature file not found:\n"
                f"{FEATURE_FILE}"
            )

        with open(
            FEATURE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            columns = json.load(file)

        if not isinstance(
            columns,
            list,
        ):
            raise ValueError(
                "PaySim feature file must contain a list."
            )

        _feature_columns = columns

    return _feature_columns


# -------------------------------------------------------------------
# Feature helpers
# -------------------------------------------------------------------

def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Convert a value to float safely.
    """

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """
    Convert a value to integer safely.
    """

    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def encode_transaction_type(
    transaction_type: Any,
) -> int:
    """
    Convert PaySim transaction type to the global numeric mapping.
    """

    if isinstance(
        transaction_type,
        str,
    ):

        normalized = (
            transaction_type
            .strip()
            .upper()
        )

        if normalized not in TRANSACTION_TYPE_MAPPING:
            raise ValueError(
                "Unknown PaySim transaction type: "
                f"{transaction_type}"
            )

        return TRANSACTION_TYPE_MAPPING[
            normalized
        ]

    numeric_type = _safe_int(
        transaction_type,
        default=-1,
    )

    if numeric_type not in (
        0,
        1,
        2,
        3,
        4,
    ):
        raise ValueError(
            f"Invalid numeric transaction type: "
            f"{transaction_type}"
        )

    return numeric_type


# -------------------------------------------------------------------
# Feature construction
# -------------------------------------------------------------------

def build_paysim_features(
    transaction: dict[str, Any],
) -> pd.DataFrame:
    """
    Build the exact model input dataframe for one PaySim transaction.
    """

    step = _safe_float(
        transaction.get("step")
    )

    transaction_type = encode_transaction_type(
        transaction.get(
            "type",
            transaction.get(
                "transaction_type",
                0,
            ),
        )
    )

    amount = _safe_float(
        transaction.get("amount")
    )

    sender_balance_before = _safe_float(
        transaction.get(
            "oldbalanceOrg",
            transaction.get(
                "sender_balance_before",
                0.0,
            ),
        )
    )

    sender_balance_after = _safe_float(
        transaction.get(
            "newbalanceOrig",
            transaction.get(
                "sender_balance_after",
                0.0,
            ),
        )
    )

    receiver_balance_before = _safe_float(
        transaction.get(
            "oldbalanceDest",
            transaction.get(
                "receiver_balance_before",
                0.0,
            ),
        )
    )

    receiver_balance_after = _safe_float(
        transaction.get(
            "newbalanceDest",
            transaction.get(
                "receiver_balance_after",
                0.0,
            ),
        )
    )

    is_flagged_fraud = _safe_int(
        transaction.get(
            "isFlaggedFraud",
            transaction.get(
                "is_flagged_fraud",
                0,
            ),
        )
    )

    # ---------------------------------------------------------------
    # Derived features
    # ---------------------------------------------------------------

    sender_balance_change = (
        sender_balance_before
        - sender_balance_after
    )

    receiver_balance_change = (
        receiver_balance_after
        - receiver_balance_before
    )

    sender_balance_error = abs(
        sender_balance_before
        - amount
        - sender_balance_after
    )

    receiver_balance_error = abs(
        receiver_balance_before
        + amount
        - receiver_balance_after
    )

    sender_zero_balance_after = int(
        sender_balance_after == 0
    )

    receiver_zero_balance_before = int(
        receiver_balance_before == 0
    )

    if sender_balance_before > 0:

        amount_to_sender_balance_ratio = (
            amount
            / sender_balance_before
        )

    else:

        amount_to_sender_balance_ratio = 0.0

    amount_exceeds_sender_balance = int(
        amount
        > sender_balance_before
    )

    # ---------------------------------------------------------------
    # PaySim-derived time proxies
    #
    # PaySim "step" represents a time step.
    # The original preprocessing pipeline used:
    #   hour_proxy = step % 24
    #   day_proxy  = step // 24
    # ---------------------------------------------------------------

    hour_proxy = (
        int(step)
        % 24
    )

    day_proxy = (
        int(step)
        // 24
    )

    # ---------------------------------------------------------------
    # Account-type proxies
    #
    # PaySim account names beginning with "C" represent customers.
    # Other account names represent merchant/bank-style accounts.
    # ---------------------------------------------------------------

    origin = str(
        transaction.get(
            "nameOrig",
            transaction.get(
                "origin",
                "",
            ),
        )
    )

    destination = str(
        transaction.get(
            "nameDest",
            transaction.get(
                "destination",
                "",
            ),
        )
    )

    origin_is_customer = int(
        origin.startswith("C")
    )

    destination_is_customer = int(
        destination.startswith("C")
    )

    same_account_type = int(
        origin_is_customer
        == destination_is_customer
    )

    feature_values = {
        "step": step,
        "transaction_type": transaction_type,
        "amount": amount,
        "sender_balance_before": sender_balance_before,
        "sender_balance_after": sender_balance_after,
        "sender_balance_change": sender_balance_change,
        "sender_balance_error": sender_balance_error,
        "sender_zero_balance_after": sender_zero_balance_after,
        "receiver_balance_before": receiver_balance_before,
        "receiver_balance_after": receiver_balance_after,
        "receiver_balance_change": receiver_balance_change,
        "receiver_balance_error": receiver_balance_error,
        "receiver_zero_balance_before": receiver_zero_balance_before,
        "amount_to_sender_balance_ratio": amount_to_sender_balance_ratio,
        "amount_exceeds_sender_balance": amount_exceeds_sender_balance,
        "hour_proxy": hour_proxy,
        "day_proxy": day_proxy,
        "is_flagged_fraud": is_flagged_fraud,
        "origin_is_customer": origin_is_customer,
        "destination_is_customer": destination_is_customer,
        "same_account_type": same_account_type,
    }

    feature_columns = load_feature_columns()

    missing = [
        column
        for column in feature_columns
        if column not in feature_values
    ]

    if missing:
        raise ValueError(
            "Unable to construct required PaySim features: "
            f"{missing}"
        )

    # IMPORTANT:
    # Reorder columns exactly as used during training.
    features = pd.DataFrame(
        [
            {
                column: feature_values[column]
                for column in feature_columns
            }
        ]
    )

    return features


# -------------------------------------------------------------------
# Prediction
# -------------------------------------------------------------------

def predict_paysim_fraud_probability(
    transaction: dict[str, Any],
) -> float:
    """
    Return the PaySim model's fraud probability for one transaction.
    """

    model = load_paysim_model()

    features = build_paysim_features(
        transaction
    )

    probability = model.predict_proba(
        features
    )[0][1]

    return float(
        max(
            0.0,
            min(
                1.0,
                probability,
            ),
        )
    )


def predict_paysim(
    transaction: dict[str, Any],
) -> dict[str, Any]:
    """
    Return a structured PaySim prediction.
    """

    probability = (
        predict_paysim_fraud_probability(
            transaction
        )
    )

    return {
        "ml_probability": probability,
        "model": "paysim_fraud_model",
    }


# -------------------------------------------------------------------
# Module test
# -------------------------------------------------------------------

if __name__ == "__main__":

    sample_transaction = {
        "step": 100,
        "type": "TRANSFER",
        "amount": 5000.0,
        "nameOrig": "C123456789",
        "oldbalanceOrg": 10000.0,
        "newbalanceOrig": 5000.0,
        "nameDest": "C987654321",
        "oldbalanceDest": 2000.0,
        "newbalanceDest": 7000.0,
        "isFlaggedFraud": 0,
    }

    result = predict_paysim(
        sample_transaction
    )

    print(
        "PaySim predictor test:"
    )

    print(
        f"ML probability: "
        f"{result['ml_probability']:.6f}"
    )

    print(
        f"Model: "
        f"{result['model']}"
    )