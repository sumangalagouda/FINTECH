import networkx as nx
from app.models.transaction import Transaction


def perform_cross_analysis(case_id: str, graph):

    results = {
        "cross_links": [],
        "hidden_paths": []
    }

    transactions = Transaction.query.filter_by(
        case_id=case_id
    ).all()

    account_statements = {}

    # -----------------------------------
    # Build account -> statements mapping
    # -----------------------------------

    for t in transactions:

        stmt = t.statement_id

        if t.sender_account:

            account_statements.setdefault(
                t.sender_account,
                set()
            ).add(stmt)

        if t.receiver_account:

            account_statements.setdefault(
                t.receiver_account,
                set()
            ).add(stmt)

    # -----------------------------------
    # Cross-linked accounts
    # -----------------------------------

    bridge_accounts = []

    for acc, stmts in account_statements.items():

        if len(stmts) > 1:

            bridge_accounts.append(acc)

            total_amount = 0

            if acc in graph.nodes:

                node = graph.nodes[acc]

                total_amount = (
                    node.get("total_received", 0)
                    + node.get("total_sent", 0)
                )

            role = "intermediary"

            if graph.degree(acc) >= 4:
                role = "hub"

            results["cross_links"].append({
                "account": acc,
                "appears_in_statements": list(stmts),
                "role": role,
                "total_amount_handled": total_amount,
                "risk_score": 88
            })

    # -----------------------------------
    # Hidden Path Discovery
    # -----------------------------------

    for bridge in bridge_accounts:

        try:

            # Find outgoing paths up to length 4
            for target in graph.nodes():

                if target == bridge:
                    continue

                try:

                    paths = list(
                        nx.all_simple_paths(
                            graph,
                            source=bridge,
                            target=target,
                            cutoff=4
                        )
                    )

                    for path in paths:

                        if len(path) < 2:
                            continue

                        total_amount = 0

                        for i in range(len(path) - 1):

                            u = path[i]
                            v = path[i + 1]

                            if isinstance(
                                graph,
                                nx.MultiDiGraph
                            ):

                                edge = max(
                                    graph[u][v].values(),
                                    key=lambda x:
                                    x.get(
                                        "weight",
                                        0
                                    )
                                )

                            else:

                                edge = graph[u][v]

                            total_amount += edge.get(
                                "weight",
                                0
                            )

                        stmts = list(
                            account_statements[
                                bridge
                            ]
                        )

                        if len(stmts) >= 2:

                            results[
                                "hidden_paths"
                            ].append({

                                "from_statement":
                                    stmts[0],

                                "to_statement":
                                    stmts[1],

                                "path":
                                    path,

                                "total_amount":
                                    total_amount
                            })

                except nx.NetworkXNoPath:
                    continue

        except Exception:
            continue

    # Remove duplicate paths

    seen = set()
    unique_paths = []

    for p in results["hidden_paths"]:

        key = tuple(p["path"])

        if key not in seen:

            seen.add(key)
            unique_paths.append(p)

    results["hidden_paths"] = unique_paths

    return results