"""
Z-Sentinel Model Router.

Routes fraud prediction requests to the configured model.

Supported models:
    - existing
    - paysim

The router returns a normalized prediction structure
regardless of which model is selected.
"""

from __future__ import annotations

from typing import Any

from config.model_config import normalize_model_name
from src.detection.prediction_adapter import (
    predict_with_existing_model,
    predict_with_paysim,
)


def predict_transaction(
    transaction: dict,
    model: str = "existing",
    existing_model: Any = None,
) -> dict:
    """
    Predict fraud probability using the selected model.

    Parameters
    ----------
    transaction:
        Transaction dictionary.

    model:
        Model to use:
            - "existing"
            - "paysim"

    existing_model:
        Loaded existing Z-Sentinel model.
        Required only when model="existing".

    Returns
    -------
    dict
        Normalized prediction result.
    """

    selected_model = normalize_model_name(
        model
    )

    if selected_model == "paysim":
        return predict_with_paysim(
            transaction
        )

    if selected_model == "existing":
        if existing_model is None:
            raise ValueError(
                "existing_model is required "
                "when model='existing'."
            )

        return predict_with_existing_model(
            existing_model,
            transaction,
        )

    # normalize_model_name() already validates
    # this, but keep an explicit guard here.
    raise ValueError(
        f"Unsupported model: {selected_model}"
    )


def is_model_available(
    model: str,
) -> bool:
    """
    Check whether a supported model name is available.

    This checks the configured model type rather
    than loading model files.
    """

    try:
        normalize_model_name(model)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Z-SENTINEL MODEL ROUTER")
    print("=" * 70)

    sample_transaction = {
        "step": 1,
        "type": "TRANSFER",
        "amount": 181.0,
        "nameOrig": "C100001",
        "oldbalanceOrg": 181.0,
        "newbalanceOrig": 0.0,
        "nameDest": "C200001",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 181.0,
        "isFlaggedFraud": 0,
    }

    print("\nTesting PaySim routing...")

    result = predict_transaction(
        transaction=sample_transaction,
        model="paysim",
    )

    print(
        f"Model          : "
        f"{result['model']}"
    )

    print(
        f"Source         : "
        f"{result['prediction_source']}"
    )

    print(
        f"ML probability : "
        f"{result['ml_probability']:.6f}"
    )

    print("\nModel availability:")

    for model_name in (
        "existing",
        "paysim",
        "invalid",
    ):
        print(
            f"  {model_name:<10} -> "
            f"{is_model_available(model_name)}"
        )

    print("\nModel router test complete.")