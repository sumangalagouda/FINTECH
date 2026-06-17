import networkx as nx


def discover_relationships(graph):

    results = []

    # ----------------------------------
    # Create simple graph for centrality
    # calculations (avoids MultiDiGraph
    # degree inflation)
    # ----------------------------------

    simple_graph = nx.DiGraph(graph)

    # ----------------------------------
    # Hub Account Detection
    # ----------------------------------

    try:

        deg_centrality = nx.degree_centrality(
            simple_graph
        )

        for node, score in deg_centrality.items():

            if score > 0.5 and simple_graph.degree(node) > 4:

                connected_accounts = list(
                    set(
                        list(
                            simple_graph.successors(node)
                        )
                        +
                        list(
                            simple_graph.predecessors(node)
                        )
                    )
                )

                results.append({
                    "relationship_type":
                        "hub_account",

                    "account":
                        node,

                    "connected_accounts":
                        connected_accounts,

                    "centrality_score":
                        round(score, 3),

                    "risk_implication":
                        f"This account connects "
                        f"{len(connected_accounts)} "
                        f"otherwise separate accounts"
                })

    except Exception:
        pass

    # ----------------------------------
    # Bridge Account Detection
    # ----------------------------------

    try:

        bet_centrality = nx.betweenness_centrality(
            simple_graph
        )

        for node, score in bet_centrality.items():

            if score > 0.10:

                connected_accounts = list(
                    set(
                        list(
                            simple_graph.successors(node)
                        )
                        +
                        list(
                            simple_graph.predecessors(node)
                        )
                    )
                )

                results.append({
                    "relationship_type":
                        "bridge_account",

                    "account":
                        node,

                    "connected_accounts":
                        connected_accounts,

                    "centrality_score":
                        round(score, 3),

                    "risk_implication":
                        "This account connects "
                        "separate clusters of "
                        "transactions"
                })

    except Exception:
        pass

    # ----------------------------------
    # Common Beneficiary
    # ----------------------------------

    for node in simple_graph.nodes():

        predecessors = list(
            simple_graph.predecessors(node)
        )

        if len(predecessors) >= 3:

            results.append({

                "relationship_type":
                    "common_beneficiary",

                "account":
                    node,

                "connected_accounts":
                    predecessors,

                "centrality_score":
                    0.0,

                "risk_implication":
                    f"This account receives "
                    f"funds from "
                    f"{len(predecessors)} "
                    f"different sources"
            })

    # ----------------------------------
    # Common Source
    # ----------------------------------

    for node in simple_graph.nodes():

        successors = list(
            simple_graph.successors(node)
        )

        if len(successors) >= 3:

            results.append({

                "relationship_type":
                    "common_source",

                "account":
                    node,

                "connected_accounts":
                    successors,

                "centrality_score":
                    0.0,

                "risk_implication":
                    f"This account sends "
                    f"funds to "
                    f"{len(successors)} "
                    f"different targets"
            })

    # ----------------------------------
    # Circular Cluster Detection
    # ----------------------------------

    try:

        cycles = list(
            nx.simple_cycles(
                simple_graph
            )
        )

        for cycle in cycles:

            if len(cycle) >= 4:

                results.append({

                    "relationship_type":
                        "circular_cluster",

                    "accounts":
                        cycle,

                    "centrality_score":
                        0.0,

                    "risk_implication":
                        "Closed circular "
                        "transfer network "
                        "detected"
                })

    except Exception:
        pass

    return results