from config.settings import settings
from src.data.generator import save_demo_data


if __name__ == "__main__":

    output_path = (
        settings.sample_data_dir
        / "demo_transactions.csv"
    )

    save_demo_data(
        output_path,
        n=5000,
        seed=42,
    )

    print(
        f"Demo data created: {output_path}"
    )