import networkx as nx
from datetime import datetime


def find_layering_chains(graph: nx.MultiDiGraph):

    results = []

    max_depth = 10

    def get_edge_data(u, v):
        """
        MultiDiGraph returns:
        graph[u][v] = {
            0: {...},
            1: {...}
        }

        Take first edge.
        """
        edge_dict = graph[u][v]

        if not edge_dict:
            return None

        return next(iter(edge_dict.values()))

    def dfs(current_node, current_path, current_amount, current_date):

        if len(current_path) >= 4:

            chain_str = " → ".join(current_path)

            transactions_involved = []

            for i in range(len(current_path) - 1):

                u = current_path[i]
                v = current_path[i + 1]

                edge_data = get_edge_data(u, v)

                if edge_data:
                    txn_id = edge_data.get("txn_id")

                    if txn_id:
                        transactions_involved.append(txn_id)

            results.append({
                "detector": "LayeringChain",
                "triggered": True,
                "score": 85,
                "reason": f"Potential layering chain detected: {chain_str}",
                "transactions_involved": transactions_involved,
                "severity": "high",
                "metadata": {
                    "chain": current_path,
                    "chain_length": len(current_path) - 1,
                    "hop_count": len(current_path) - 1
                }
            })

        if len(current_path) >= max_depth:
            return

        for neighbor in graph.successors(current_node):

            if neighbor in current_path:
                continue

            edge_data = get_edge_data(current_node, neighbor)

            if not edge_data:
                continue

            next_amount = edge_data.get("weight", 0.0)

            next_date_str = edge_data.get("date")

            if not next_date_str:
                continue

            try:
                next_date = datetime.strptime(
                    next_date_str,
                    "%Y-%m-%d"
                ).date()
            except:
                continue

            # Time window check
            if current_date:

                time_diff = (
                    next_date - current_date
                ).days * 24

                if time_diff < 0:
                    continue

                if time_diff > 72:
                    continue

            # Amount similarity check
            if current_amount > 0:

                # allow up to 30% drop
                if next_amount < 0.70 * current_amount:
                    continue

            dfs(
                neighbor,
                current_path + [neighbor],
                next_amount,
                next_date
            )

    for node in graph.nodes:

        for neighbor in graph.successors(node):

            edge_data = get_edge_data(node, neighbor)

            if not edge_data:
                continue

            amt = edge_data.get("weight", 0.0)

            date_str = edge_data.get("date")

            if not date_str:
                continue

            try:

                start_date = datetime.strptime(
                    date_str,
                    "%Y-%m-%d"
                ).date()

                dfs(
                    neighbor,
                    [node, neighbor],
                    amt,
                    start_date
                )

            except:
                continue

    # Deduplicate chains

    unique_results = {}

    for result in results:

        key = tuple(result["metadata"]["chain"])

        unique_results[key] = result

    return list(unique_results.values())