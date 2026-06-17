def score_layering_chain(chain_data, graph):
    """
    Scores a layering chain detected by the LayeringChain detector.
    Compatible with NetworkX MultiDiGraph.
    """

    chain_length = chain_data.get("chain_length", 0)
    chain_nodes = chain_data.get("chain", [])

    if chain_length < 3:
        return None

    # Base score
    score = 60

    # Extra hops bonus
    extra_hops = max(0, chain_length - 3)
    score += min(30, extra_hops * 10)

    avg_hop_hours = 0
    amount_similarity_pct = 100

    if len(chain_nodes) > 1:

        min_amount = float("inf")
        max_amount = 0

        for i in range(len(chain_nodes) - 1):

            u = chain_nodes[i]
            v = chain_nodes[i + 1]

            try:
                # MultiDiGraph support
                edge_dict = graph[u][v]

                if not edge_dict:
                    continue

                first_edge = next(iter(edge_dict.values()))

                amt = float(first_edge.get("weight", 0.0))

                min_amount = min(min_amount, amt)
                max_amount = max(max_amount, amt)

            except Exception:
                continue

        if max_amount > 0 and min_amount != float("inf"):
            amount_similarity_pct = (
                min_amount / max_amount
            ) * 100

        # Similar amounts = suspicious layering
        if amount_similarity_pct > 90:
            score += 20
        elif amount_similarity_pct > 80:
            score += 10

    # Beneficiary novelty calculation
    all_new = True
    new_count = 0

    for node in chain_nodes[1:]:

        txn_count = graph.nodes[node].get(
            "transaction_count",
            0
        )

        if txn_count <= 2:
            new_count += 1
        else:
            all_new = False

    if all_new:
        score += 15

    # Cap score
    score = min(score, 100)

    # Severity mapping
    if score >= 91:
        severity = "critical"
    elif score >= 76:
        severity = "high"
    elif score >= 61:
        severity = "medium"
    else:
        severity = "low"

    return {
        "detector": "LayeringSeverity",
        "triggered": True,
        "score": score,
        "reason": (
            f"{chain_length}-hop layering chain, "
            f"{amount_similarity_pct:.1f}% amount similarity."
        ),
        "severity": severity,
        "metadata": {
            "chain_length": chain_length,
            "avg_hop_minutes": avg_hop_hours * 60,
            "amount_similarity_pct": round(
                amount_similarity_pct,
                1
            ),
            "beneficiary_novelty":
                f"{new_count}/{len(chain_nodes)-1} new"
        }
    }