# import networkx as nx
# from datetime import datetime


# def find_layering_chains(graph: nx.MultiDiGraph):

#     results = []

#     max_depth = 10

#     def get_edge_data(u, v):
#         """
#         MultiDiGraph returns:
#         graph[u][v] = {
#             0: {...},
#             1: {...}
#         }

#         Take first edge.
#         """
#         edge_dict = graph[u][v]

#         if not edge_dict:
#             return None

#         return next(iter(edge_dict.values()))

#     def dfs(current_node, current_path, current_amount, current_date):

#         if len(current_path) >= 4:

#             chain_str = " → ".join(current_path)

#             transactions_involved = []

#             for i in range(len(current_path) - 1):

#                 u = current_path[i]
#                 v = current_path[i + 1]

#                 edge_data = get_edge_data(u, v)

#                 if edge_data:
#                     txn_id = edge_data.get("txn_id")

#                     if txn_id:
#                         transactions_involved.append(txn_id)

#             results.append({
#                 "detector": "LayeringChain",
#                 "triggered": True,
#                 "score": 85,
#                 "reason": f"Potential layering chain detected: {chain_str}",
#                 "transactions_involved": transactions_involved,
#                 "severity": "high",
#                 "metadata": {
#                     "chain": current_path,
#                     "chain_length": len(current_path) - 1,
#                     "hop_count": len(current_path) - 1
#                 }
#             })

#         if len(current_path) >= max_depth:
#             return

#         for neighbor in graph.successors(current_node):

#             if neighbor in current_path:
#                 continue

#             edge_data = get_edge_data(current_node, neighbor)

#             if not edge_data:
#                 continue

#             next_amount = edge_data.get("weight", 0.0)

#             next_date_str = edge_data.get("date")

#             if not next_date_str:
#                 continue

#             try:
#                 next_date = datetime.strptime(
#                     next_date_str,
#                     "%Y-%m-%d"
#                 ).date()
#             except:
#                 continue

#             # Time window check
#             if current_date:

#                 time_diff = (
#                     next_date - current_date
#                 ).days * 24

#                 if time_diff < 0:
#                     continue

#                 if time_diff > 72:
#                     continue

#             # Amount similarity check
#             if current_amount > 0:

#                 # allow up to 30% drop
#                 if next_amount < 0.70 * current_amount:
#                     continue

#             dfs(
#                 neighbor,
#                 current_path + [neighbor],
#                 next_amount,
#                 next_date
#             )

#     for node in graph.nodes:

#         for neighbor in graph.successors(node):

#             edge_data = get_edge_data(node, neighbor)

#             if not edge_data:
#                 continue

#             amt = edge_data.get("weight", 0.0)

#             date_str = edge_data.get("date")

#             if not date_str:
#                 continue

#             try:

#                 start_date = datetime.strptime(
#                     date_str,
#                     "%Y-%m-%d"
#                 ).date()

#                 dfs(
#                     neighbor,
#                     [node, neighbor],
#                     amt,
#                     start_date
#                 )

#             except:
#                 continue

#     # Deduplicate chains

#     unique_results = {}

#     for result in results:

#         key = tuple(result["metadata"]["chain"])

#         unique_results[key] = result

#     return list(unique_results.values())
import networkx as nx
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================

MIN_CHAIN_LENGTH = 3
MAX_DEPTH = 8

MAX_TIME_WINDOW_HOURS = 72
MIN_AMOUNT_RETENTION = 0.70
MIN_CHAIN_AMOUNT = 50000


# ============================================================================
# HELPERS
# ============================================================================

def get_best_edge(graph, u, v):
    """
    For MultiDiGraph:
    Choose the highest-value edge.
    """

    edge_dict = graph[u][v]

    if not edge_dict:
        return None

    return max(
        edge_dict.values(),
        key=lambda x: x.get("weight", 0)
    )


# ============================================================================
# DETECTOR
# ============================================================================

def find_layering_chains(graph: nx.MultiDiGraph):

    results = []

    # ========================================================================
    # DFS
    # ========================================================================

    def dfs(
        current_node,
        current_path,
        current_amount,
        current_date,
        txns
    ):

        hop_count = len(current_path) - 1

        # --------------------------------------------------------------------
        # DETECTION
        # --------------------------------------------------------------------

        if hop_count >= MIN_CHAIN_LENGTH:

            if current_amount >= MIN_CHAIN_AMOUNT:

                score = 60

                # More hops = more suspicious
                score += min(
                    hop_count * 5,
                    20
                )

                # Large money movement
                if current_amount >= 100000:
                    score += 10

                if current_amount >= 500000:
                    score += 10

                score = min(score, 100)

                severity = (
                    "critical"
                    if score >= 90
                    else "high"
                    if score >= 70
                    else "medium"
                )

                chain_str = " → ".join(
                    current_path
                )

                results.append({

                    "detector":
                        "LayeringChain",

                    "triggered":
                        True,

                    "score":
                        score,

                    "reason":
                        f"Potential layering chain detected: "
                        f"{chain_str}. "
                        f"₹{current_amount:,.2f} "
                        f"moved across "
                        f"{hop_count} hops.",

                    "transactions_involved":
                        txns,

                    "severity":
                        severity,

                    "metadata": {

                        "chain":
                            current_path,

                        "chain_length":
                            hop_count,

                        "hop_count":
                            hop_count,

                        "amount":
                            round(current_amount, 2)
                    }
                })

        # --------------------------------------------------------------------
        # DEPTH LIMIT
        # --------------------------------------------------------------------

        if hop_count >= MAX_DEPTH:
            return

        # --------------------------------------------------------------------
        # CONTINUE DFS
        # --------------------------------------------------------------------

        for neighbor in graph.successors(
            current_node
        ):

            if neighbor in current_path:
                continue

            edge = get_best_edge(
                graph,
                current_node,
                neighbor
            )

            if not edge:
                continue

            next_amount = float(
                edge.get("weight", 0)
            )

            if next_amount <= 0:
                continue

            # --------------------------------------------------------------
            # AMOUNT RETENTION
            # --------------------------------------------------------------

            if (
                current_amount > 0
                and next_amount
                < current_amount
                * MIN_AMOUNT_RETENTION
            ):
                continue

            # --------------------------------------------------------------
            # DATE HANDLING
            # --------------------------------------------------------------

            date_str = edge.get("date")

            if not date_str:
                continue

            try:

                next_date = (
                    datetime
                    .fromisoformat(date_str)
                )

            except Exception:

                continue

            # --------------------------------------------------------------
            # TIME WINDOW
            # --------------------------------------------------------------

            if current_date:

                hours = (
                    next_date
                    - current_date
                ).total_seconds() / 3600

                if hours < 0:
                    continue

                if hours > MAX_TIME_WINDOW_HOURS:
                    continue

            txn_id = edge.get("txn_id")

            dfs(
                neighbor,
                current_path + [neighbor],
                next_amount,
                next_date,
                txns + (
                    [txn_id]
                    if txn_id
                    else []
                )
            )

    # ========================================================================
    # START DFS
    # ========================================================================

    for node in graph.nodes:

        for neighbor in graph.successors(node):

            edge = get_best_edge(
                graph,
                node,
                neighbor
            )

            if not edge:
                continue

            amount = float(
                edge.get("weight", 0)
            )

            if amount < MIN_CHAIN_AMOUNT:
                continue

            date_str = edge.get("date")

            if not date_str:
                continue

            try:

                start_date = (
                    datetime
                    .fromisoformat(date_str)
                )

            except Exception:

                continue

            txn_id = edge.get("txn_id")

            dfs(
                neighbor,
                [node, neighbor],
                amount,
                start_date,
                [txn_id] if txn_id else []
            )

    # ========================================================================
    # DEDUPLICATION
    # ========================================================================

    unique = {}

    for result in results:

        key = tuple(
            result["metadata"]["chain"]
        )

        if (
            key not in unique
            or result["score"]
            > unique[key]["score"]
        ):
            unique[key] = result

    return sorted(
        unique.values(),
        key=lambda x: x["score"],
        reverse=True
    )