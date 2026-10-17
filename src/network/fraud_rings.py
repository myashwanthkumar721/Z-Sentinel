"""
Coordinated fraud-ring detection for Z-Sentinel.

Identifies groups of accounts that share infrastructure such as
devices, IP addresses, or merchants.

The goal is to detect coordinated activity rather than analyzing
transactions only in isolation.
"""

from __future__ import annotations

import networkx as nx


def build_account_relationship_graph(
    graph: nx.Graph,
) -> nx.Graph:
    """
    Build an account-to-account graph from the original
    heterogeneous transaction graph.

    Two accounts become connected when they share at least
    one device, IP address, or merchant.
    """

    account_graph = nx.Graph()

    account_nodes = [
        node
        for node, attributes in graph.nodes(data=True)
        if attributes.get("node_type") == "account"
    ]

    account_graph.add_nodes_from(account_nodes)

    for index, account in enumerate(account_nodes):

        account_neighbors = set(
            graph.neighbors(account)
        )

        for other_account in account_nodes[
            index + 1:
        ]:

            other_neighbors = set(
                graph.neighbors(other_account)
            )

            shared = account_neighbors.intersection(
                other_neighbors
            )

            if shared:

                account_graph.add_edge(
                    account,
                    other_account,
                    shared_nodes=len(shared),
                )

    return account_graph


def find_connected_accounts(
    graph: nx.Graph,
    account_id: str,
) -> list[dict]:
    """
    Find accounts connected to the specified account.

    Returns information about shared infrastructure.
    """

    account_node = (
        account_id
        if account_id.startswith("account:")
        else f"account:{account_id}"
    )

    if account_node not in graph:
        return []

    account_graph = (
        build_account_relationship_graph(
            graph
        )
    )

    if account_node not in account_graph:
        return []

    connected = []

    for neighbor in account_graph.neighbors(
        account_node
    ):

        edge_data = account_graph.edges[
            account_node,
            neighbor
        ]

        identifier = graph.nodes[
            neighbor
        ].get(
            "identifier",
            neighbor,
        )

        connected.append(
            {
                "account_id":
                    str(identifier),

                "shared_connections":
                    int(
                        edge_data.get(
                            "shared_nodes",
                            0,
                        )
                    ),
            }
        )

    connected.sort(
        key=lambda item:
            item["shared_connections"],
        reverse=True,
    )

    return connected


def calculate_fraud_ring_score(
    graph: nx.Graph,
    account_id: str,
) -> float:
    """
    Calculate a normalized coordinated-network score.

    The score increases when an account is connected to
    multiple other accounts through shared infrastructure.
    """

    connected = find_connected_accounts(
        graph,
        account_id,
    )

    if not connected:
        return 0.0

    connection_count = len(
        connected
    )

    shared_connection_strength = sum(
        item["shared_connections"]
        for item in connected
    )

    score = (
        connection_count * 0.5
        + shared_connection_strength * 0.25
    )

    return float(
        min(
            max(
                score / 10.0,
                0.0,
            ),
            1.0,
        )
    )


def detect_fraud_rings(
    graph: nx.Graph,
    minimum_accounts: int = 3,
) -> list[dict]:
    """
    Detect connected groups of accounts.

    A group is considered interesting when it contains
    at least ``minimum_accounts`` accounts.
    """

    account_graph = (
        build_account_relationship_graph(
            graph
        )
    )

    rings = []

    for component in nx.connected_components(
        account_graph
    ):

        if len(component) < minimum_accounts:
            continue

        accounts = []

        for node in component:

            identifier = account_graph.nodes[
                node
            ].get(
                "identifier"
            )

            if identifier is None:

                identifier = str(
                    node
                ).replace(
                    "account:",
                    "",
                    1,
                )

            accounts.append(
                str(identifier)
            )

        accounts.sort()

        subgraph = account_graph.subgraph(
            component
        )

        rings.append(
            {
                "accounts":
                    accounts,

                "account_count":
                    len(accounts),

                "network_density":
                    float(
                        nx.density(
                            subgraph
                        )
                    ),
            }
        )

    rings.sort(
        key=lambda item:
            item["account_count"],
        reverse=True,
    )

    return rings