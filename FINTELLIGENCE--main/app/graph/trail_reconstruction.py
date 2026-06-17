import networkx as nx
from datetime import datetime

def format_duration(minutes):

    if minutes < 60:
        return f"{minutes} minutes"

    hours = minutes // 60

    if hours < 24:
        return f"{hours} hours"

    days = hours // 24

    if days < 30:
        return f"{days} days"

    months = days // 30

    return f"{months} months"
def calculate_minutes_between(date1, date2):
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")

        return int(
            (d2 - d1).total_seconds() / 60
        )

    except Exception:
        return 0


def get_best_edge(graph, u, v):

    edge_data = graph[u][v]

    if isinstance(graph, nx.MultiDiGraph):
        return max(
            edge_data.values(),
            key=lambda e: e.get("weight", 0)
        )

    return edge_data


def reconstruct_trail(graph: nx.MultiDiGraph, start_txn_id=None):

    start_u = None
    start_v = None

    # ------------------------------------------------
    # Start from explicit transaction if supplied
    # ------------------------------------------------

    if start_txn_id:

        if isinstance(graph, nx.MultiDiGraph):

            for u, v, key, data in graph.edges(
                keys=True,
                data=True
            ):
                if data.get("txn_id") == start_txn_id:
                    start_u = u
                    start_v = v
                    break

        else:

            for u, v, data in graph.edges(data=True):
                if data.get("txn_id") == start_txn_id:
                    start_u = u
                    start_v = v
                    break

    # ------------------------------------------------
    # Otherwise pick earliest suspicious transaction
    # ------------------------------------------------

    if not start_u or not start_v:

        earliest_date = None

        if isinstance(graph, nx.MultiDiGraph):

            for u, v, key, data in graph.edges(
                keys=True,
                data=True
            ):

                amt = data.get("weight", 0)

                if amt < 100000:
                    continue

                try:

                    txn_date = datetime.strptime(
                        data.get("date"),
                        "%Y-%m-%d"
                    )

                except:
                    continue

                if (
                    earliest_date is None
                    or txn_date < earliest_date
                ):
                    earliest_date = txn_date
                    start_u = u
                    start_v = v

        else:

            for u, v, data in graph.edges(data=True):

                amt = data.get("weight", 0)

                if amt < 100000:
                    continue

                try:

                    txn_date = datetime.strptime(
                        data.get("date"),
                        "%Y-%m-%d"
                    )

                except:
                    continue

                if (
                    earliest_date is None
                    or txn_date < earliest_date
                ):
                    earliest_date = txn_date
                    start_u = u
                    start_v = v

    if not start_u or not start_v:
        return {
            "trail": [],
            "total_hops": 0,
            "total_amount": 0,
            "total_time_hours": 0
        }

    first_edge = get_best_edge(
        graph,
        start_u,
        start_v
    )

    total_amount = first_edge.get(
        "weight",
        0.0
    )

    trail = []

    current_u = start_u
    current_v = start_v

    hop = 0

    total_minutes = 0

    visited = set()

    while current_u and current_v and hop < 10:

        edge_data = get_best_edge(
            graph,
            current_u,
            current_v
        )

        current_date = edge_data.get("date")

        node_data = graph.nodes[current_u]

        next_v = None
        next_edge = None

        max_amt = -1

        for neighbor in graph.successors(current_v):

            if (current_v, neighbor) in visited:
                continue

            edge_info = get_best_edge(
                graph,
                current_v,
                neighbor
            )

            amt = edge_info.get(
                "weight",
                0
            )

            next_date = edge_info.get(
                "date"
            )

            try:

                if current_date and next_date:

                    current_dt = datetime.strptime(
                        current_date,
                        "%Y-%m-%d"
                    )

                    next_dt = datetime.strptime(
                        next_date,
                        "%Y-%m-%d"
                    )

                    if next_dt < current_dt:
                        continue

            except:
                continue

            if amt > max_amt:

                max_amt = amt
                next_v = neighbor
                next_edge = edge_info

        time_held = 0

        if next_edge:

            next_date = next_edge.get("date")

            time_held = max(
                0,
                calculate_minutes_between(
                    current_date,
                    next_date
                )
            )

            total_minutes += time_held

        trail.append({
            "hop": hop,
            "account": current_u,
            "label":
                "Origin Account"
                if hop == 0
                else f"Intermediary {hop}",

            "amount_received":
                node_data.get(
                    "total_received",
                    0
                ),

            "amount_sent":
                node_data.get(
                    "total_sent",
                    0
                ),

            "time_held_minutes":
                time_held,
            "time_held_human":
                format_duration(time_held),
            "date":
                current_date,

            "risk_flag":
                "origin"
                if hop == 0
                else "layering",

            "txn_id":
                edge_data.get(
                    "txn_id"
                )
        })

        visited.add(
            (current_u, current_v)
        )

        if next_v:

            current_u = current_v
            current_v = next_v
            hop += 1

        else:

            trail.append({
                "hop": hop + 1,
                "account": current_v,
                "label":
                    "Destination Account",

                "amount_received":
                    graph.nodes[current_v].get(
                        "total_received",
                        0
                    ),

                "amount_sent":
                    graph.nodes[current_v].get(
                        "total_sent",
                        0
                    ),

                "time_held_minutes": 0,

                "date":
                    current_date,

                "risk_flag":
                    "destination",

                "txn_id": None
            })

            break

    return {
        "trail": trail,
        "total_hops": len(trail) - 1,
        "total_amount": total_amount,
        "total_time_hours":
            round(total_minutes / 60, 2)
    }