"""
Identify suspicious account relationships.
"""

from __future__ import annotations

import networkx as nx


def find_suspicious_accounts(
    graph: nx.Graph,
    minimum_degree: int = 8,
) -> list[dict]:
    """
    Find accounts whose relationship count reaches the
    suspicious-network threshold.
    """

    suspicious: list[dict] = []

    for node, attributes in graph.nodes(data=True):

        if attributes.get("node_type") != "account":
            continue

        degree = int(graph.degree(node))

        if degree < minimum_degree:
            continue

        account_id = str(
            attributes.get("identifier", node)
        )

        suspicious.append(
            {
                "account_id": account_id,
                "network_degree": degree,
                "reason": (
                    "Account has unusually many connected "
                    "devices, IPs, or merchants."
                ),
            }
        )

    suspicious.sort(
        key=lambda item: item["network_degree"],
        reverse=True,
    )

    return suspicious


def account_relationships(
    graph: nx.Graph,
    account_id: str,
) -> list[dict]:
    """
    Return all direct relationships for an account.
    """

    account_node = (
        account_id
        if account_id.startswith("account:")
        else f"account:{account_id}"
    )

    if account_node not in graph:
        return []

    relationships = []

    for neighbor in graph.neighbors(account_node):

        attributes = graph.nodes[neighbor]

        relationships.append(
            {
                "node": neighbor,
                "node_type": attributes.get(
                    "node_type",
                    "unknown",
                ),
                "identifier": attributes.get(
                    "identifier",
                    neighbor,
                ),
                "relationship": graph.edges[
                    account_node,
                    neighbor
                ].get(
                    "relationship",
                    "connected",
                ),
            }
        )

    return relationships