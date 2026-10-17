from config.settings import settings

from src.data.cleaner import (
    clean_transactions,
)

from src.data.generator import (
    generate_transactions,
)

from src.data.validator import (
    validate_transactions,
)


if __name__ == "__main__":

    df = generate_transactions(
        n=5000,
        seed=42,
    )

    df = clean_transactions(
        df
    )

    validate_transactions(
        df,
        require_target=True,
    )

    output_path = (
        settings.processed_data_dir
        / "transactions_processed.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    print(
        f"Processed data saved: {output_path}"
    )