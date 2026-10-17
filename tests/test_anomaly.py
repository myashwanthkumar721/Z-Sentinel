from src.anomaly.detector import (
    anomaly_score,
    train_anomaly_model,
)

from src.data.generator import (
    generate_transactions,
)


def test_anomaly_model(tmp_path):

    df = generate_transactions(
        500,
        seed=42,
    )

    model = train_anomaly_model(
        df,
        tmp_path,
    )

    transaction = (
        df.iloc[0].to_dict()
    )

    score = anomaly_score(
        model,
        transaction,
    )

    assert 0 <= score <= 1