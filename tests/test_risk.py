from src.risk.risk_engine import (
    evaluate_risk,
)


def test_risk_output():

    transaction = {

        "amount": 100,

        "transactions_last_1h": 1,

        "amount_last_1h": 100,

        "device_age_days": 300,

        "is_new_device": 0,

        "failed_attempts": 0,

        "is_international": 0,

        "merchant_risk": 0.1,

        "ip_risk": 0.1,

        "network_degree": 2,
    }

    result = evaluate_risk(
        transaction,
        0.1,
        0.1,
        0.1,
    )

    assert (
        0
        <= result["risk_score"]
        <= 100
    )

    assert result["decision"] in {
        "ALLOW",
        "VERIFY",
        "HOLD",
    }

    assert result["reasons"]