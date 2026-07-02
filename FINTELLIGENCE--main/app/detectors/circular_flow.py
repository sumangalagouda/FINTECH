# import networkx as nx
# from datetime import datetime

# def detect_circular_flow(graph: nx.DiGraph):
#     """
#     Finds all cycles in the graph.
#     Output Canonical Detector Schema
#     """
#     results = []
    
#     # nx.simple_cycles returns lists of nodes forming cycles
#     # For directed graphs, simple cycles are elementary circuits
#     cycles = list(nx.simple_cycles(graph))
    
#     for cycle in cycles:
#         # We need at least 2 nodes to form a meaningful cycle, though technically self-loops are 1
#         if len(cycle) < 2:
#             continue
            
#         total_amount = 0.0
#         time_span_days = 0
#         min_date = None
#         max_date = None
#         transactions_involved = []
        
#         # Calculate cycle details
#         for i in range(len(cycle)):
#             u = cycle[i]
#             v = cycle[(i + 1) % len(cycle)]
            
#             # Handle both DiGraph and MultiDiGraph
#             if graph.has_edge(u, v):
#                 edges_dict = graph[u][v]
                
#                 # If it's a MultiDiGraph, edges_dict has integer keys for multiple edges
#                 if isinstance(graph, nx.MultiDiGraph):
#                     edge_list = list(edges_dict.values())
#                 else:
#                     # For standard DiGraph
#                     edge_list = [edges_dict]
                
#                 for edge_data in edge_list:
#                     total_amount += edge_data.get('weight', 0.0)
#                     transactions_involved.append(edge_data.get('txn_id'))
                    
#                     t_date = edge_data.get('date')
#                     if t_date:
#                         try:
#                             d = datetime.strptime(t_date, "%Y-%m-%d").date()
#                             if min_date is None or d < min_date: min_date = d
#                             if max_date is None or d > max_date: max_date = d
#                         except ValueError:
#                             pass
        
#         if min_date and max_date:
#             time_span_days = (max_date - min_date).days
            
#         score = 50
#         if len(cycle) > 3:
#             score += 10 * len(cycle)
#         if total_amount > 100000:
#             score += 15
#         if time_span_days < 7:
#             score += 10
            
#         # Assuming we can check if all accounts are new by looking at transaction_count <= 2 or similar
#         # For this detector, we will just add it if they are all new (simplified proxy: transaction_count == 2)
#         all_new = True
#         for node in cycle:
#             if graph.nodes[node].get('transaction_count', 0) > 2:
#                 all_new = False
#                 break
#         if all_new:
#             score += 15
            
#         severity = "low"
#         if score > 60: severity = "medium"
#         if score > 75: severity = "high"
#         if score > 90: severity = "critical"
        
#         cycle_str = "→".join(cycle) + "→" + cycle[0]
        
#         results.append({
#             "detector": "CircularFlow",
#             "triggered": True,
#             "score": min(score, 100),
#             "reason": f"Circular flow: {cycle_str}. Total ₹{total_amount} cycled in {time_span_days} days.",
#             "transactions_involved": [t for t in transactions_involved if t],
#             "severity": severity,
#             "metadata": {
#                 "cycle": cycle,
#                 "total_amount": total_amount,
#                 "time_span_days": time_span_days
#             }
#         })
        
#     return results
import networkx as nx
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================

MAX_CYCLE_LENGTH = 5
HIGH_VALUE_THRESHOLD = 100000
FAST_CYCLE_DAYS = 7


# ============================================================================
# DETECTOR
# ============================================================================

def detect_circular_flow(graph: nx.MultiDiGraph):

    results = []

    # ========================================================================
    # LIMIT CYCLE SEARCH
    # ========================================================================

    cycles = [
        cycle
        for cycle in nx.simple_cycles(graph)
        if 2 <= len(cycle) <= MAX_CYCLE_LENGTH
    ]

    if not cycles:
        return []

    # ========================================================================
    # ANALYZE EACH CYCLE
    # ========================================================================

    for cycle in cycles:

        total_amount = 0.0
        transactions_involved = []

        min_date = None
        max_date = None

        # --------------------------------------------------------------------
        # EDGE ANALYSIS
        # --------------------------------------------------------------------

        for i in range(len(cycle)):

            u = cycle[i]
            v = cycle[(i + 1) % len(cycle)]

            if not graph.has_edge(u, v):
                continue

            edge_data_container = graph[u][v]

            if isinstance(graph, nx.MultiDiGraph):

                edges = edge_data_container.values()

            else:

                edges = [edge_data_container]

            for edge in edges:

                total_amount += float(
                    edge.get("weight", 0)
                )

                txn_id = edge.get("txn_id")

                if txn_id:
                    transactions_involved.append(
                        txn_id
                    )

                # ------------------------------------------------------------
                # ISO DATE SUPPORT
                # ------------------------------------------------------------

                date_str = edge.get("date")

                if date_str:

                    try:

                        d = (
                            datetime
                            .fromisoformat(date_str)
                            .date()
                        )

                        if (
                            min_date is None
                            or d < min_date
                        ):
                            min_date = d

                        if (
                            max_date is None
                            or d > max_date
                        ):
                            max_date = d

                    except Exception:
                        pass

        transactions_involved = list(
            set(transactions_involved)
        )

        # --------------------------------------------------------------------
        # TIME SPAN
        # --------------------------------------------------------------------

        time_span_days = 0

        if min_date and max_date:

            time_span_days = (
                max_date - min_date
            ).days

        # --------------------------------------------------------------------
        # SCORING
        # --------------------------------------------------------------------

        score = 50

        # Longer cycles are more suspicious
        if len(cycle) >= 4:

            score += min(
                len(cycle) * 5,
                20
            )

        # High-value movement
        if total_amount >= HIGH_VALUE_THRESHOLD:

            score += 15

        # Rapid circulation
        if (
            time_span_days > 0
            and time_span_days <= FAST_CYCLE_DAYS
        ):

            score += 10

        # New accounts bonus
        all_new = all(
            graph.nodes[node].get(
                "transaction_count",
                0
            ) <= 2
            for node in cycle
        )

        if all_new:

            score += 15

        score = min(score, 100)

        # --------------------------------------------------------------------
        # SEVERITY
        # --------------------------------------------------------------------

        if score >= 90:

            severity = "critical"

        elif score >= 70:

            severity = "high"

        elif score >= 50:

            severity = "medium"

        else:

            severity = "low"

        cycle_str = (
            " → ".join(cycle)
            + f" → {cycle[0]}"
        )

        # --------------------------------------------------------------------
        # OUTPUT
        # --------------------------------------------------------------------

        results.append({

            "detector": "CircularFlow",

            "triggered": True,

            "score": score,

            "reason": (
                f"Detected circular movement: "
                f"{cycle_str}. "
                f"₹{total_amount:,.2f} circulated "
                f"over {time_span_days} days."
            ),

            "transactions_involved":
                transactions_involved,

            "severity":
                severity,

            "metadata": {

                "cycle":
                    cycle,

                "cycle_length":
                    len(cycle),

                "total_amount":
                    round(total_amount, 2),

                "time_span_days":
                    time_span_days,

                "all_accounts_new":
                    all_new
            }
        })

    return sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )