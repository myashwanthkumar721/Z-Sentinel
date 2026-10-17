"""
Z-Sentinel Prediction Adapter.

Provides a common interface for fraud-probability prediction
across the existing Z-Sentinel model and the PaySim model.

The adapter does not modify either trained model.
"""

from __future__ import annotations

from typing import Any

from src.detection.predictor import predict_fraud_probability
from src.detection.paysim_predictor import predict_paysim


def predict_with_existing_model(
    model: Any,
    transaction: dict,
) -> dict:
    """
    Run the existing Z-Sentinel fraud model.

    Returns a normalized prediction structure.
    """

    probability = float(
        predict_fraud_probability(
            model,
            transaction,
        )
    )

    return {
        "ml_probability": probability,
        "model": "z_sentinel_fraud_model",
        "prediction_source": "existing_model",
    }


def predict_with_paysim(
    transaction: dict,
) -> dict:
    """
    Run the PaySim fraud model.

    Returns the same normalized prediction structure
    as the existing-model path.
    """

    result = predict_paysim(
        transaction
    )

    return {
        "ml_probability": float(
            result["ml_probability"]
        ),
        "model": result.get(
            "model",
            "paysim_fraud_model",
        ),
        "prediction_source": "paysim",
    }


def normalize_prediction(
    probability: float,
    model: str,
    prediction_source: str,
) -> dict:
    """
    Build a normalized prediction response.

    Probability is safely clamped to the [0, 1] range.
    """

    probability = max(
        0.0,
        min(
            1.0,
            float(probability),
        ),
    )

    return {
        "ml_probability": probability,
        "model": str(model),
        "prediction_source": str(
            prediction_source
        ),
    }


if __name__ == "__main__":
    print("=" * 70)
    print("Z-SENTINEL PREDICTION ADAPTER")
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

    result = predict_with_paysim(
        sample_transaction
    )

    print(
        f"ML probability : "
        f"{result['ml_probability']:.6f}"
    )

    print(
        f"Model          : "
        f"{result['model']}"
    )

    print(
        f"Source         : "
        f"{result['prediction_source']}"
    )

    print("\nPrediction adapter test complete.")