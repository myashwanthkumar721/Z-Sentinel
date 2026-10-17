"""
Build transaction relationship graphs for Z-Sentinel.

The graph represents relationships between:
    Account -> Device
    Account -> IP
    Account -> Merchant

Network analysis can then identify accounts connected to
many devices, IP addresses, or merchants.
"""

from __future__ import annotations

from typing import Iterable

import networkx as nx
import pandas as pd


REQUIRED_COLUMNS = {
    "account_id",
    "device_id",
    "ip_address",
    "merchant_id",
}


def build_transaction_graph(
    transactions: pd.DataFrame,
) -> nx.Graph:
    """
    Build an undirected relationship graph from transactions.

    Node types:
        account
        device
        ip
        merchant

    Edges represent observed relationships.
    """

    missing = REQUIRED_COLUMNS - set(transactions.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    graph = nx.Graph()

    for _, row in transactions.iterrows():

        account = str(row["account_id"])
        device = str(row["device_id"])
        ip = str(row["ip_address"])
        merchant = str(row["merchant_id"])

        account_node = f"account:{account}"
        device_node = f"device:{device}"
        ip_node = f"ip:{ip}"
        merchant_node = f"merchant:{merchant}"

        graph.add_node(
            account_node,
            node_type="account",
            identifier=account,
        )

        graph.add_node(
            device_node,
            node_type="device",
            identifier=device,
        )

        graph.add_node(
            ip_node,
            node_type="ip",
            identifier=ip,
        )

        graph.add_node(
            merchant_node,
            node_type="merchant",
            identifier=merchant,
        )

        graph.add_edge(
            account_node,
            device_node,
            relationship="uses_device",
        )

        graph.add_edge(
            account_node,
            ip_node,
            relationship="uses_ip",
        )

        graph.add_edge(
            account_node,
            merchant_node,
            relationship="uses_merchant",
        )

    return graph


def account_subgraph(graph: nx.Graph) -> nx.Graph:
    """
    Return only account nodes and their direct relationships.
    """

    account_nodes = [
        node
        for node, attributes in graph.nodes(data=True)
        if attributes.get("node_type") == "account"
    ]

    return graph.subgraph(account_nodes).copy()


def get_account_nodes(graph: nx.Graph) -> list[str]:
    """Return all account nodes from the graph."""

    return [
        node
        for node, attributes in graph.nodes(data=True)
        if attributes.get("node_type") == "account"
    ]