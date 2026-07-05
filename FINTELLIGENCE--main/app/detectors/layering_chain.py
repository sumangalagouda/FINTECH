import networkx as nx
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

MIN_CHAIN_LENGTH = 3
MAX_DEPTH = 8

MAX_TIME_WINDOW_HOURS = 72
MIN_AMOUNT_RETENTION = 0.70
MIN_CHAIN_AMOUNT = 0

# ============================================================================
# HELPERS
# ============================================================================

def get_best_edge(graph, u, v):
    edge_dict = graph[u][v]
    if not edge_dict:
        return None
    return max(edge_dict.values(), key=lambda x: x.get("weight", 0))

def is_valid_node(node_name):
    if not isinstance(node_name, str):
        return False
    name_upper = node_name.upper()
    invalids = [
        "BLKRTGS", "IMPS", "OPENING BALANCE", "PRIMARY_ACCOUNT", 
        "UNKNOWN", "FEE", "GST", "CHARGE"
    ]
    for inv in invalids:
        if inv in name_upper:
            return False
    return True

# ============================================================================
# DETECTOR
# ============================================================================

def find_layering_chains(graph: nx.MultiDiGraph):
    results = []

    def dfs(current_node, current_path, current_amount, current_date, txns):
        hop_count = len(current_path) - 1

        if hop_count >= MIN_CHAIN_LENGTH:
            if current_amount >= MIN_CHAIN_AMOUNT:
                score = 60
                score += min(hop_count * 5, 20)
                if current_amount >= 100000:
                    score += 10
                if current_amount >= 500000:
                    score += 10
                score = min(score, 100)

                severity = "critical" if score >= 90 else "high" if score >= 70 else "medium"
                chain_str = " -> ".join(current_path)

                results.append({
                    "detector": "LayeringChain",
                    "triggered": True,
                    "score": score,
                    "reason": f"Potential layering chain detected: {chain_str}. ₹{current_amount:,.2f} moved across {hop_count} hops.",
                    "transactions_involved": txns,
                    "severity": severity,
                    "metadata": {
                        "chain": current_path,
                        "chain_length": hop_count,
                        "hop_count": hop_count,
                        "amount": round(current_amount, 2)
                    }
                })

        if hop_count >= MAX_DEPTH:
            return

        for neighbor in graph.successors(current_node):
            if neighbor in current_path:
                continue
            
            if not is_valid_node(neighbor):
                continue

            edge = get_best_edge(graph, current_node, neighbor)
            if not edge:
                continue

            next_amount = float(edge.get("weight", 0))
            if next_amount <= 0:
                continue

            # AMOUNT RETENTION
            if next_amount < MIN_AMOUNT_RETENTION * current_amount:
                continue

            # TIME WINDOW
            date_str = edge.get("date")
            next_date = None
            if date_str:
                try:
                    next_date = datetime.fromisoformat(date_str)
                except Exception:
                    pass
            
            if current_date and next_date:
                time_diff = (next_date - current_date).total_seconds() / 3600.0
                if time_diff < 0 or time_diff > MAX_TIME_WINDOW_HOURS:
                    continue

            txn_id = edge.get("txn_id")
            dfs(
                neighbor,
                current_path + [neighbor],
                next_amount,
                next_date,
                txns + ([txn_id] if txn_id else [])
            )

    for node in graph.nodes:
        if not is_valid_node(node):
            continue

        for neighbor in graph.successors(node):
            if not is_valid_node(neighbor):
                continue

            edge = get_best_edge(graph, node, neighbor)
            if not edge:
                continue

            amount = float(edge.get("weight", 0))
            if amount < MIN_CHAIN_AMOUNT:
                continue

            date_str = edge.get("date")
            start_date = None
            if date_str:
                try:
                    start_date = datetime.fromisoformat(date_str)
                except Exception:
                    pass

            txn_id = edge.get("txn_id")
            dfs(
                neighbor,
                [node, neighbor],
                amount,
                start_date,
                [txn_id] if txn_id else []
            )

    unique = {}
    for result in results:
        key = tuple(result["metadata"]["chain"])
        if key not in unique or result["score"] > unique[key]["score"]:
            unique[key] = result

    return sorted(unique.values(), key=lambda x: (x["metadata"]["chain_length"], x["score"]), reverse=True)[:3]