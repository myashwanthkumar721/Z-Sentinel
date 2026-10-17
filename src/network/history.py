"""
Persistent transaction network history for Z-Sentinel.

Stores the relationship fields required to rebuild the
historical NetworkX fraud graph.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from config.settings import settings
from src.network.graph_builder import build_transaction_graph


HISTORY_FILE = (
    settings.processed_data_dir
    / "network_history.json"
)


REQUIRED_COLUMNS = {
    "account_id",
    "device_id",
    "ip_address",
    "merchant_id",
}


def _ensure_history_directory() -> None:
    """Create the processed data directory if needed."""

    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


def load_network_history() -> pd.DataFrame:
    """
    Load previously analyzed transaction relationships.

    Returns an empty DataFrame when no history exists.
    """

    _ensure_history_directory()

    if not HISTORY_FILE.exists():
        return pd.DataFrame(
            columns=sorted(REQUIRED_COLUMNS)
        )

    try:

        with HISTORY_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

    except (
        json.JSONDecodeError,
        OSError,
    ):

        return pd.DataFrame(
            columns=sorted(REQUIRED_COLUMNS)
        )

    if not isinstance(data, list) or not data:

        return pd.DataFrame(
            columns=sorted(REQUIRED_COLUMNS)
        )

    dataframe = pd.DataFrame(data)

    missing = (
        REQUIRED_COLUMNS
        - set(dataframe.columns)
    )

    if missing:

        raise ValueError(
            "Network history is missing columns: "
            f"{sorted(missing)}"
        )

    return dataframe


def save_network_transaction(
    transaction: dict,
) -> None:
    """
    Add a transaction relationship record to history.
    """

    missing = (
        REQUIRED_COLUMNS
        - set(transaction.keys())
    )

    if missing:

        raise ValueError(
            "Transaction is missing network fields: "
            f"{sorted(missing)}"
        )

    history = load_network_history()

    new_record = {
        column: str(transaction[column])
        for column in REQUIRED_COLUMNS
    }

    history = pd.concat(
        [
            history,
            pd.DataFrame([new_record]),
        ],
        ignore_index=True,
    )

    records = history.to_dict(
        orient="records"
    )

    _ensure_history_directory()

    with HISTORY_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            records,
            file,
            indent=2,
        )


def build_historical_network():
    """
    Build a NetworkX graph from all stored transactions.
    """

    history = load_network_history()

    if history.empty:

        return build_transaction_graph(
            pd.DataFrame(
                columns=sorted(
                    REQUIRED_COLUMNS
                )
            )
        )

    return build_transaction_graph(
        history
    )


def clear_network_history() -> None:
    """
    Clear stored network history.

    Useful for restarting a demonstration.
    """

    if HISTORY_FILE.exists():

        HISTORY_FILE.unlink()