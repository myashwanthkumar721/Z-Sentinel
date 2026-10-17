import pandas as pd

from src.network.graph_builder import (
    build_transaction_graph,
)
from src.network.network_analysis import (
    account_network_degree,
    account_network_score,
    calculate_network_signals,
    network_summary,
)
from src.network.suspicious_networks import (
    account_relationships,
    find_suspicious_accounts,
)


def sample_transactions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "account_id": "ACC-001",
                "device_id": "DEV-001",
                "ip_address": "10.0.0.1",
                "merchant_id": "MER-001",
            },
            {
                "account_id": "ACC-001",
                "device_id": "DEV-002",
                "ip_address": "10.0.0.2",
                "merchant_id": "MER-002",
            },
            {
                "account_id": "ACC-002",
                "device_id": "DEV-003",
                "ip_address": "10.0.0.3",
                "merchant_id": "MER-003",
            },
        ]
    )


def test_graph_building():
    df = sample_transactions()

    graph = build_transaction_graph(df)

    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0


def test_account_degree():
    df = sample_transactions()

    graph = build_transaction_graph(df)

    degree = account_network_degree(
        graph,
        "ACC-001",
    )

    assert degree == 6


def test_network_score():
    df = sample_transactions()

    graph = build_transaction_graph(df)

    score = account_network_score(
        graph,
        "ACC-001",
    )

    assert 0.0 <= score <= 1.0
    assert score == 0.75


def test_network_signals():
    df = sample_transactions()

    graph = build_transaction_graph(df)

    signals = calculate_network_signals(graph)

    assert "ACC-001" in signals
    assert "ACC-002" in signals

    for score in signals.values():
        assert 0.0 <= score <= 1.0


def test_network_summary():
    df = sample_transactions()

    graph = build_transaction_graph(df)

    summary = network_summary(graph)

    assert summary["accounts"] == 2
    assert summary["devices"] == 3
    assert summary["ips"] == 3
    assert summary["merchants"] == 3
    assert summary["nodes"] == 11
    assert summary["edges"] == 9


def test_account_relationships():
    df = sample_transactions()

    graph = build_transaction_graph(df)

    relationships = account_relationships(
        graph,
        "ACC-001",
    )

    assert len(relationships) == 6


def test_suspicious_accounts():
    df = pd.DataFrame(
        [
            {
                "account_id": "ACC-SUSPICIOUS",
                "device_id": "DEV-001",
                "ip_address": "10.0.0.1",
                "merchant_id": "MER-001",
            },
            {
                "account_id": "ACC-SUSPICIOUS",
                "device_id": "DEV-002",
                "ip_address": "10.0.0.2",
                "merchant_id": "MER-002",
            },
            {
                "account_id": "ACC-SUSPICIOUS",
                "device_id": "DEV-003",
                "ip_address": "10.0.0.3",
                "merchant_id": "MER-003",
            },
        ]
    )

    graph = build_transaction_graph(df)

    suspicious = find_suspicious_accounts(
        graph,
        minimum_degree=8,
    )

    assert len(suspicious) == 1
    assert suspicious[0]["account_id"] == "ACC-SUSPICIOUS"
    assert suspicious[0]["network_degree"] == 9