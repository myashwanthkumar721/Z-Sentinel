from functools import lru_cache
from unittest import result

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from api.schemas import (
    TransactionRequest,
    TransactionResponse,
)
from database.repository import (
    save_result,
    transaction_exists,
)
from src.streaming.processor import TransactionProcessor


router = APIRouter()


@lru_cache(maxsize=2)
def get_processor(
    model_name: str,
) -> TransactionProcessor:
    """
    Return a cached transaction processor for
    the requested detection model.
    """

    try:
        return TransactionProcessor(
            model_name=model_name
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/health")
def health():
    """
    API health check.
    """

    return {
        "status": "ok",
        "service": "Z-Sentinel",
    }


@router.post(
    "/analyze",
    response_model=TransactionResponse,
)
def analyze(
    transaction: TransactionRequest,
):
    """
    Analyze one transaction through the complete
    Z-Sentinel detection pipeline.
    """

    data = transaction.model_dump()

    selected_model = data.pop(
        "model",
        "existing",
    )

    transaction_id = str(
        data["transaction_id"]
    )

    # --------------------------------------------------
    # Duplicate protection
    # --------------------------------------------------
    # Check before running the expensive detection
    # pipeline so duplicate requests cannot trigger
    # unnecessary ML/network/history processing.
    # --------------------------------------------------

    try:
        if transaction_exists(
            transaction_id
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Transaction ID already exists: "
                    f"{transaction_id}"
                ),
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Transaction lookup failed: "
                f"{exc}"
            ),
        ) from exc

    # --------------------------------------------------
    # Detection pipeline
    # --------------------------------------------------

    try:
        processor = get_processor(
            selected_model
        )

        result = processor.process(
            transaction=data,
            save_history=True,
        )

        response = {
            "transaction_id": data[
                "transaction_id"
            ],
            "account_id": data[
                "account_id"
            ],
            "amount": data[
                "amount"
            ],
            "model_name": result[
                "model_name"
            ],
            "prediction_model": result[
                "prediction_model"
            ],
            "prediction_source": result[
                "prediction_source"
            ],
            "ml_probability": result[
                "ml_probability"
            ],
            "anomaly_score": result[
                "anomaly_score"
            ],
            "network_score": result[
                "network_score"
            ],
            "fraud_ring_score": result[
                "fraud_ring_score"
            ],
            "risk_score": result[
                "risk_score"
            ],
            "base_decision": result[
                "base_decision"
            ],
            "decision": result[
                "decision"
            ],
            "reasons": result[
                "reasons"
            ],
            "signals": result[
                "signals"
            ],
        
            "investigation": result[
                "risk_result"
        
            ].get(
            "investigation",
            {},
        ),
        }
        try:
            save_result(response)

        except IntegrityError as exc:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Transaction ID already exists: "
                    f"{transaction_id}"
                ),
            ) from exc

        return response

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Transaction analysis failed: "
                f"{exc}"
            ),
        ) from exc