from config.settings import settings

from src.data.generator import (
    generate_transactions,
)

from src.detection.fraud_model import (
    train_fraud_model,
)

from src.detection.predictor import (
    predict_fraud_probability,
)


def test_fraud_model(tmp_path):

    df = generate_transactions(
        500,
        seed=42,
    )

    model, metrics = train_fraud_model(
        df,
        tmp_path,
    )

    assert model is not None
    assert "accuracy" in metrics

    transaction = df.iloc[0].to_dict()

    probability = (
        predict_fraud_probability(
            model,
            transaction,
        )
    )

    assert 0 <= probability <= 1