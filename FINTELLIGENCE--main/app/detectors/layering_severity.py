# def score_layering_chain(chain_data, graph):
#     """
#     Scores a layering chain detected by the LayeringChain detector.
#     Compatible with NetworkX MultiDiGraph.
#     """

#     chain_length = chain_data.get("chain_length", 0)
#     chain_nodes = chain_data.get("chain", [])

#     if chain_length < 3:
#         return None

#     # Base score
#     score = 60

#     # Extra hops bonus
#     extra_hops = max(0, chain_length - 3)
#     score += min(30, extra_hops * 10)

#     avg_hop_hours = 0
#     amount_similarity_pct = 100

#     if len(chain_nodes) > 1:

#         min_amount = float("inf")
#         max_amount = 0

#         for i in range(len(chain_nodes) - 1):

#             u = chain_nodes[i]
#             v = chain_nodes[i + 1]

#             try:
#                 # MultiDiGraph support
#                 edge_dict = graph[u][v]

#                 if not edge_dict:
#                     continue

#                 first_edge = next(iter(edge_dict.values()))

#                 amt = float(first_edge.get("weight", 0.0))

#                 min_amount = min(min_amount, amt)
#                 max_amount = max(max_amount, amt)

#             except Exception:
#                 continue

#         if max_amount > 0 and min_amount != float("inf"):
#             amount_similarity_pct = (
#                 min_amount / max_amount
#             ) * 100

#         # Similar amounts = suspicious layering
#         if amount_similarity_pct > 90:
#             score += 20
#         elif amount_similarity_pct > 80:
#             score += 10

#     # Beneficiary novelty calculation
#     all_new = True
#     new_count = 0

#     for node in chain_nodes[1:]:

#         txn_count = graph.nodes[node].get(
#             "transaction_count",
#             0
#         )

#         if txn_count <= 2:
#             new_count += 1
#         else:
#             all_new = False

#     if all_new:
#         score += 15

#     # Cap score
#     score = min(score, 100)

#     # Severity mapping
#     if score >= 91:
#         severity = "critical"
#     elif score >= 76:
#         severity = "high"
#     elif score >= 61:
#         severity = "medium"
#     else:
#         severity = "low"

#     return {
#         "detector": "LayeringSeverity",
#         "triggered": True,
#         "score": score,
#         "reason": (
#             f"{chain_length}-hop layering chain, "
#             f"{amount_similarity_pct:.1f}% amount similarity."
#         ),
#         "severity": severity,
#         "metadata": {
#             "chain_length": chain_length,
#             "avg_hop_minutes": avg_hop_hours * 60,
#             "amount_similarity_pct": round(
#                 amount_similarity_pct,
#                 1
#             ),
#             "beneficiary_novelty":
#                 f"{new_count}/{len(chain_nodes)-1} new"
#         }
#     }

from datetime import datetime


# ============================================================================
# LAYERING SEVERITY SCORER
# ============================================================================

def score_layering_chain(chain_data, graph):

    chain_length = chain_data.get(
        "chain_length",
        0
    )

    chain_nodes = chain_data.get(
        "chain",
        []
    )

    if chain_length < 3:
        return None

    # ========================================================================
    # BASE SCORE
    # ========================================================================

    score = 60

    # Extra hops bonus
    extra_hops = max(
        0,
        chain_length - 3
    )

    score += min(
        30,
        extra_hops * 10
    )

    # ========================================================================
    # AMOUNT CONSISTENCY + TIMING
    # ========================================================================

    min_amount = float("inf")
    max_amount = 0

    hop_durations = []

    previous_date = None

    for i in range(len(chain_nodes) - 1):

        u = chain_nodes[i]
        v = chain_nodes[i + 1]

        try:

            edge_dict = graph[u][v]

            if not edge_dict:
                continue

            # Highest-value edge
            edge = max(
                edge_dict.values(),
                key=lambda x: x.get(
                    "weight",
                    0
                )
            )

            amount = float(
                edge.get(
                    "weight",
                    0
                )
            )

            min_amount = min(
                min_amount,
                amount
            )

            max_amount = max(
                max_amount,
                amount
            )

            date_str = edge.get("date")

            if date_str:

                current_date = (
                    datetime
                    .fromisoformat(date_str)
                )

                if previous_date:

                    hours = (
                        current_date
                        - previous_date
                    ).total_seconds() / 3600

                    if hours >= 0:
                        hop_durations.append(
                            hours
                        )

                previous_date = current_date

        except Exception:
            continue

    # ========================================================================
    # AMOUNT SIMILARITY
    # ========================================================================

    amount_similarity_pct = 100.0

    if (
        max_amount > 0
        and min_amount != float("inf")
    ):

        amount_similarity_pct = (
            min_amount
            / max_amount
        ) * 100

    if amount_similarity_pct >= 95:

        score += 20

    elif amount_similarity_pct >= 85:

        score += 10

    # ========================================================================
    # HOP SPEED
    # ========================================================================

    avg_hop_hours = (
        sum(hop_durations)
        / len(hop_durations)
    ) if hop_durations else 0

    if (
        avg_hop_hours > 0
        and avg_hop_hours <= 6
    ):

        score += 10

    # ========================================================================
    # BENEFICIARY NOVELTY
    # ========================================================================

    new_count = 0

    for node in chain_nodes[1:]:

        txn_count = graph.nodes[node].get(
            "transaction_count",
            0
        )

        if txn_count <= 2:
            new_count += 1

    if new_count == len(chain_nodes) - 1:

        score += 15

    elif new_count >= (
        len(chain_nodes) // 2
    ):

        score += 8

    # ========================================================================
    # FINALIZE
    # ========================================================================

    score = min(score, 100)

    if score >= 90:

        severity = "critical"

    elif score >= 75:

        severity = "high"

    elif score >= 60:

        severity = "medium"

    else:

        severity = "low"

    # ========================================================================
    # OUTPUT
    # ========================================================================

    return {

        "detector":
            "LayeringSeverity",

        "triggered":
            True,

        "score":
            score,

        "reason": (
            f"{chain_length}-hop layering chain "
            f"with {amount_similarity_pct:.1f}% "
            f"amount consistency and "
            f"{avg_hop_hours:.1f} hours "
            f"average hop delay."
        ),

        "severity":
            severity,

        "metadata": {

            "chain_length":
                chain_length,

            "avg_hop_minutes":
                round(
                    avg_hop_hours * 60,
                    1
                ),

            "amount_similarity_pct":
                round(
                    amount_similarity_pct,
                    1
                ),

            "beneficiary_novelty":
                f"{new_count}/"
                f"{len(chain_nodes)-1} new"
        }
    }