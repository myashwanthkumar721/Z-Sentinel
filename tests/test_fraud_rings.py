"""
Tests for coordinated fraud-ring detection.
"""

import pandas as pd

from src.network.graph_builder import (
    build_transaction_graph,
)

from src.network.fraud_rings import (
    build_account_relationship_graph,
    find_connected_accounts,
    calculate_fraud_ring_score,
    detect_fraud_rings,
)


def create_test_transactions():

    return pd.DataFrame(
        [
            {
                "account_id": "ACC-A",
                "device_id": "DEV-SHARED",
                "ip_address": "10.0.0.1",
                "merchant_id": "MERCHANT-1",
            },
            {
                "account_id": "ACC-B",
                "device_id": "DEV-SHARED",
                "ip_address": "10.0.0.2",
                "merchant_id": "MERCHANT-2",
            },
            {
                "account_id": "ACC-C",
                "device_id": "DEV-SHARED",
                "ip_address": "10.0.0.3",
                "merchant_id": "MERCHANT-3",
            },
            {
                "account_id": "ACC-D",
                "device_id": "DEV-D",
                "ip_address": "10.0.0.4",
                "merchant_id": "MERCHANT-4",
            },
        ]
    )


def test_account_relationship_graph():

    transactions = (
        create_test_transactions()
    )

    graph = build_transaction_graph(
        transactions
    )

    account_graph = (
        build_account_relationship_graph(
            graph
        )
    )

    assert (
        account_graph.has_edge(
            "account:ACC-A",
            "account:ACC-B",
        )
    )

    assert (
        account_graph.has_edge(
            "account:ACC-A",
            "account:ACC-C",
        )
    )

    assert (
        not account_graph.has_edge(
            "account:ACC-A",
            "account:ACC-D",
        )
    )


def test_connected_accounts():

    transactions = (
        create_test_transactions()
    )

    graph = build_transaction_graph(
        transactions
    )

    connected = (
        find_connected_accounts(
            graph,
            "ACC-A",
        )
    )

    account_ids = {
        item["account_id"]
        for item in connected
    }

    assert account_ids == {
        "ACC-B",
        "ACC-C",
    }


def test_fraud_ring_score():

    transactions = (
        create_test_transactions()
    )

    graph = build_transaction_graph(
        transactions
    )

    score = (
        calculate_fraud_ring_score(
            graph,
            "ACC-A",
        )
    )

    assert score > 0.0
    assert score <= 1.0


def test_detect_fraud_rings():

    transactions = (
        create_test_transactions()
    )

    graph = build_transaction_graph(
        transactions
    )

    rings = detect_fraud_rings(
        graph,
        minimum_accounts=3,
    )

    assert len(rings) == 1

    assert rings[0][
        "account_count"
    ] == 3

    assert set(
        rings[0]["accounts"]
    ) == {
        "ACC-A",
        "ACC-B",
        "ACC-C",
    }