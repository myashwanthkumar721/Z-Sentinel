from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


class TransactionRequest(
    BaseModel
):
    transaction_id: str

    account_id: str

    device_id: str = "unknown"

    ip_address: str = "0.0.0.0"

    merchant_id: str = "unknown"

    amount: float = Field(
        default=0,
        ge=0,
    )

    model: Literal["existing", "paysim"] = "existing"

    hour: int = Field(
        default=12,
        ge=0,
        le=23,
    )

    transactions_last_1h: int = Field(
        default=0,
        ge=0,
    )

    amount_last_1h: float = Field(
        default=0,
        ge=0,
    )

    account_age_days: int = Field(
        default=365,
        ge=0,
    )

    device_age_days: int = Field(
        default=365,
        ge=0,
    )

    is_new_device: int = Field(
        default=0,
        ge=0,
        le=1,
    )

    is_international: int = Field(
        default=0,
        ge=0,
        le=1,
    )

    failed_attempts: int = Field(
        default=0,
        ge=0,
    )

    merchant_risk: float = Field(
        default=0,
        ge=0,
        le=1,
    )

    ip_risk: float = Field(
        default=0,
        ge=0,
        le=1,
    )

    network_degree: int = Field(
        default=1,
        ge=0,
    )

    # PaySim-specific fields

    step: int = Field(
        default=0,
        ge=0,
    )

    type: str = "PAYMENT"

    oldbalanceOrg: float = Field(
        default=0,
        ge=0,
    )

    newbalanceOrig: float = Field(
        default=0,
        ge=0,
    )

    oldbalanceDest: float = Field(
        default=0,
        ge=0,
    )

    newbalanceDest: float = Field(
        default=0,
        ge=0,
    )


class TransactionResponse(
    BaseModel
):

    transaction_id: str

    account_id: str

    amount: float

    model_name: str

    prediction_model: str

    prediction_source: str

    ml_probability: float

    anomaly_score: float

    network_score: float

    fraud_ring_score: float

    risk_score: float

    base_decision: str

    decision: str

    reasons: list[str]

    signals: dict
    
    investigation: dict