from pathlib import Path

import pandas as pd


def load_csv(
    path: str | Path,
) -> pd.DataFrame:

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Data file not found: {file_path}"
        )

    if file_path.suffix.lower() != ".csv":
        raise ValueError(
            "Expected a CSV file."
        )

    df = pd.read_csv(file_path)

    if df.empty:
        raise ValueError(
            "CSV file is empty."
        )

    return df