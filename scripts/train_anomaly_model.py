from config.settings import settings

from src.anomaly.detector import (
    train_anomaly_model,
)

from src.data.generator import (
    generate_transactions,
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
        "Training anomaly model..."
    )

    train_anomaly_model(
        df,
        settings.model_dir,
    )

    print(
        "Anomaly model trained successfully."
    )