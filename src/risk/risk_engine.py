"""
Z-Sentinel risk scoring and decision engine.

Combines machine-learning, anomaly, network, coordinated
fraud-ring, velocity and device signals into one explainable
risk score.

Phase 15 adds structured investigation evidence while
preserving the existing risk calculation and decision logic.
"""

from __future__ import annotations

from config.thresholds import (
    ALLOW_MAX,
    VERIFY_MAX,
    ML_WEIGHT,
    ANOMALY_WEIGHT,
    NETWORK_WEIGHT,
    FRAUD_RING_WEIGHT,
    VELOCITY_WEIGHT,
    DEVICE_WEIGHT,
)

from src.risk.explanations import explain_transaction


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """Clamp a value to a specified range."""

    return float(
        min(
            max(
                float(value),
                minimum,
            ),
            maximum,
        )
    )


def _velocity_signal(
    transaction: dict,
) -> float:
    """
    Convert transaction velocity into a normalized risk signal.
    """

    velocity = float(
        transaction.get(
            "transactions_last_1h",
            0,
        )
    )

    return _clamp(
        velocity / 20.0
    )


def _device_signal(
    transaction: dict,
) -> float:
    """
    Calculate device-related risk.
    """

    new_device = float(
        transaction.get(
            "is_new_device",
            0,
        )
    )

    international = float(
        transaction.get(
            "is_international",
            0,
        )
    )

    return _clamp(
        (new_device * 0.7)
        + (international * 0.3)
    )


def _build_investigation_evidence(
    transaction: dict,
    signals: dict,
    network_degree: int,
    connected_accounts: list | None,
    risk_score: float,
    decision: str,
) -> dict:
    """
    Build structured investigation evidence.

    This section does not change the risk calculation.
    It converts the already-calculated signals into a
    structured format suitable for analyst dashboards,
    APIs and investigation workflows.
    """

    # --------------------------------------------------------
    # Risk contributions
    # --------------------------------------------------------

    risk_contributions = {
        "ml": round(
            signals["ml_probability"]
            * ML_WEIGHT
            * 100.0,
            2,
        ),

        "anomaly": round(
            signals["anomaly_score"]
            * ANOMALY_WEIGHT
            * 100.0,
            2,
        ),

        "network": round(
            signals["network_score"]
            * NETWORK_WEIGHT
            * 100.0,
            2,
        ),

        "fraud_ring": round(
            signals["fraud_ring_score"]
            * FRAUD_RING_WEIGHT
            * 100.0,
            2,
        ),

        "velocity": round(
            signals["velocity_score"]
            * VELOCITY_WEIGHT
            * 100.0,
            2,
        ),

        "device": round(
            signals["device_score"]
            * DEVICE_WEIGHT
            * 100.0,
            2,
        ),
    }

    # --------------------------------------------------------
    # Transaction evidence
    # --------------------------------------------------------

    transaction_evidence = {
        "amount": float(
            transaction.get(
                "amount",
                0,
            )
        ),

        "transactions_last_1h": int(
            transaction.get(
                "transactions_last_1h",
                0,
            )
        ),

        "failed_attempts": int(
            transaction.get(
                "failed_attempts",
                0,
            )
        ),

        "is_new_device": bool(
            transaction.get(
                "is_new_device",
                0,
            )
        ),

        "is_international": bool(
            transaction.get(
                "is_international",
                0,
            )
        ),

        "merchant_risk": round(
            float(
                transaction.get(
                    "merchant_risk",
                    0,
                )
            ),
            4,
        ),

        "ip_risk": round(
            float(
                transaction.get(
                    "ip_risk",
                    0,
                )
            ),
            4,
        ),
    }

    # --------------------------------------------------------
    # Network evidence
    # --------------------------------------------------------

    connected_count = len(
        connected_accounts
        or []
    )

    network_evidence = {
        "network_degree": int(
            network_degree
        ),

        "network_score": round(
            signals["network_score"],
            4,
        ),

        "fraud_ring_score": round(
            signals["fraud_ring_score"],
            4,
        ),

        "connected_account_count": int(
            connected_count
        ),

        "connected_accounts": (
            connected_accounts
            or []
        ),
    }

    # --------------------------------------------------------
    # Decision summary
    # --------------------------------------------------------

    if decision == "ALLOW":
        decision_summary = (
            "Transaction remains below the "
            "verification threshold."
        )

    elif decision == "VERIFY":
        decision_summary = (
            "Transaction requires additional "
            "verification because its combined "
            "risk signals fall within the "
            "verification band."
        )

    else:
        decision_summary = (
            "Transaction is in the hold band "
            "because its combined risk signals "
            "exceed the verification threshold."
        )

    return {
        "risk_contributions":
            risk_contributions,

        "transaction_evidence":
            transaction_evidence,

        "network_evidence":
            network_evidence,

        "decision_summary":
            decision_summary,

        "risk_score":
            risk_score,

        "decision":
            decision,
    }


def evaluate_risk(
    transaction: dict,
    ml_probability: float,
    anomaly_score: float,
    network_score: float,
    fraud_ring_score: float = 0.0,
    network_degree: int = 0,
    connected_accounts: list | None = None,
) -> dict:
    """
    Calculate the final Z-Sentinel risk score.

    Parameters
    ----------
    transaction:
        Transaction feature dictionary.

    ml_probability:
        Supervised ML fraud probability, 0 to 1.

    anomaly_score:
        Behavioral anomaly score, 0 to 1.

    network_score:
        Relationship-network risk, 0 to 1.

    fraud_ring_score:
        Coordinated-account risk, 0 to 1.

    network_degree:
        Number of relationships in the transaction network.

    connected_accounts:
        Accounts connected to the current account.

    Returns
    -------
    dict
        Risk score, decision, signals, explanations
        and structured investigation evidence.
    """

    # --------------------------------------------------------
    # Normalize incoming signals
    # --------------------------------------------------------

    ml_probability = _clamp(
        ml_probability
    )

    anomaly_score = _clamp(
        anomaly_score
    )

    network_score = _clamp(
        network_score
    )

    fraud_ring_score = _clamp(
        fraud_ring_score
    )

    velocity_score = _velocity_signal(
        transaction
    )

    device_score = _device_signal(
        transaction
    )

    # --------------------------------------------------------
    # Weighted risk calculation
    # --------------------------------------------------------

    weighted_score = (
        ml_probability
        * ML_WEIGHT

        + anomaly_score
        * ANOMALY_WEIGHT

        + network_score
        * NETWORK_WEIGHT

        + fraud_ring_score
        * FRAUD_RING_WEIGHT

        + velocity_score
        * VELOCITY_WEIGHT

        + device_score
        * DEVICE_WEIGHT
    )

    risk_score = round(
        weighted_score * 100.0,
        2,
    )

    # --------------------------------------------------------
    # Decision
    # --------------------------------------------------------

    if risk_score <= ALLOW_MAX:

        decision = "ALLOW"

    elif risk_score <= VERIFY_MAX:

        decision = "VERIFY"

    else:

        decision = "HOLD"

    # --------------------------------------------------------
    # Signal dictionary
    # --------------------------------------------------------

    signals = {
        "ml_probability":
            round(
                ml_probability,
                4,
            ),

        "anomaly_score":
            round(
                anomaly_score,
                4,
            ),

        "network_score":
            round(
                network_score,
                4,
            ),

        "fraud_ring_score":
            round(
                fraud_ring_score,
                4,
            ),

        "velocity_score":
            round(
                velocity_score,
                4,
            ),

        "device_score":
            round(
                device_score,
                4,
            ),
    }

    # --------------------------------------------------------
    # Explainable intelligence
    # --------------------------------------------------------

    reasons = explain_transaction(
        transaction=transaction,
        signals=signals,
        network_degree=network_degree,
        connected_accounts=connected_accounts,
    )

    # --------------------------------------------------------
    # Structured investigation evidence
    # --------------------------------------------------------

    investigation = _build_investigation_evidence(
        transaction=transaction,
        signals=signals,
        network_degree=network_degree,
        connected_accounts=connected_accounts,
        risk_score=risk_score,
        decision=decision,
    )

    return {
        "risk_score":
            risk_score,

        "decision":
            decision,

        "signals":
            signals,

        "reasons":
            reasons,

        "investigation":
            investigation,
    }