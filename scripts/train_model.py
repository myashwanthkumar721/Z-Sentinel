from config.settings import settings

from src.data.generator import (
    generate_transactions,
)

from src.detection.fraud_model import (
    train_fraud_model,
)


if __name__ == "__main__":

    print(
        "Generating training data..."
    )

    df = generate_transactions(
        n=5000,
        seed=42,
    )

    print(
        "Training fraud model..."
    )

    _, metrics = train_fraud_model(
        df,
        settings.model_dir,
    )

    print(
        "\nFraud model trained successfully."
    )

    print(
        "\nMetrics:"
    )

    for key, value in metrics.items():

        if value is None:
            print(
                f"{key}: N/A"
            )
        else:
            print(
                f"{key}: {value:.4f}"
            )