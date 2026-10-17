"""
Network-based fraud signals for Z-Sentinel.

This module provides network relationship analysis while keeping
compatibility with the API layer.
"""

from __future__ import annotations

import networkx as nx


DEFAULT_SUSPICIOUS_DEGREE = 8


def account_network_degree(
    graph: nx.Graph,
    account_id: str,
) -> int:
    """
    Return the number of direct relationships for an account.
    """

    account_node = (
        account_id
        if account_id.startswith("account:")
        else f"account:{account_id}"
    )

    if account_node not in graph:
        return 0

    return int(graph.degree(account_node))


def calculate_network_signal_from_degree(
    degree: int,
    suspicious_degree: int = DEFAULT_SUSPICIOUS_DEGREE,
) -> float:
    """
    Convert a network degree into a normalized 0-1 risk signal.

    Examples:
        degree 0 -> 0.0
        degree 4 -> 0.5
        degree 8 -> 1.0
        degree 12 -> 1.0

    The score is capped at 1.0.
    """

    degree = max(0, int(degree))
    suspicious_degree = max(1, int(suspicious_degree))

    score = degree / float(suspicious_degree)

    return float(min(max(score, 0.0), 1.0))


def account_network_score(
    graph: nx.Graph,
    account_id: str,
    suspicious_degree: int = DEFAULT_SUSPICIOUS_DEGREE,
) -> float:
    """
    Calculate the normalized network risk score for an account.
    """

    degree = account_network_degree(
        graph,
        account_id,
    )

    return calculate_network_signal_from_degree(
        degree,
        suspicious_degree,
    )


def calculate_network_signals(
    graph: nx.Graph,
    suspicious_degree: int = DEFAULT_SUSPICIOUS_DEGREE,
) -> dict[str, float]:
    """
    Calculate a network risk score for every account.
    """

    results: dict[str, float] = {}

    for node, attributes in graph.nodes(data=True):

        if attributes.get("node_type") != "account":
            continue

        account_id = str(
            attributes.get("identifier", "")
        )

        results[account_id] = account_network_score(
            graph,
            account_id,
            suspicious_degree,
        )

    return results


def network_summary(
    graph: nx.Graph,
) -> dict:
    """
    Return basic graph statistics.
    """

    account_count = sum(
        1
        for _, attributes in graph.nodes(data=True)
        if attributes.get("node_type") == "account"
    )

    device_count = sum(
        1
        for _, attributes in graph.nodes(data=True)
        if attributes.get("node_type") == "device"
    )

    ip_count = sum(
        1
        for _, attributes in graph.nodes(data=True)
        if attributes.get("node_type") == "ip"
    )

    merchant_count = sum(
        1
        for _, attributes in graph.nodes(data=True)
        if attributes.get("node_type") == "merchant"
    )

    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "accounts": account_count,
        "devices": device_count,
        "ips": ip_count,
        "merchants": merchant_count,
    }