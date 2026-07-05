# import networkx as nx
# from app.models.transaction import Transaction


# def build_graph(transactions: list) -> nx.MultiDiGraph:
#     """
#     Build transaction graph from transactions.

#     Uses MultiDiGraph so multiple transactions between
#     the same sender and receiver are preserved.
#     """

#     G = nx.MultiDiGraph()

#     nodes = {}

#     for t in transactions:

#         u = t.sender_account
#         v = t.receiver_account
#         amt = float(t.amount or 0)
#         t_date = t.date

#         # Skip incomplete transactions
#         if not u or not v:
#             continue

#         # Initialize sender node
#         if u not in nodes:
#             nodes[u] = {
#                 "total_received": 0.0,
#                 "total_sent": 0.0,
#                 "transaction_count": 0,
#                 "first_seen": t_date,
#                 "last_seen": t_date,
#                 "risk_score": 0.0
#             }

#         # Initialize receiver node
#         if v not in nodes:
#             nodes[v] = {
#                 "total_received": 0.0,
#                 "total_sent": 0.0,
#                 "transaction_count": 0,
#                 "first_seen": t_date,
#                 "last_seen": t_date,
#                 "risk_score": 0.0
#             }

#         # Sender stats
#         nodes[u]["total_sent"] += amt
#         nodes[u]["transaction_count"] += 1

#         if t_date:
#             if nodes[u]["first_seen"] is None or t_date < nodes[u]["first_seen"]:
#                 nodes[u]["first_seen"] = t_date

#             if nodes[u]["last_seen"] is None or t_date > nodes[u]["last_seen"]:
#                 nodes[u]["last_seen"] = t_date

#         # Receiver stats
#         nodes[v]["total_received"] += amt
#         nodes[v]["transaction_count"] += 1

#         if t_date:
#             if nodes[v]["first_seen"] is None or t_date < nodes[v]["first_seen"]:
#                 nodes[v]["first_seen"] = t_date

#             if nodes[v]["last_seen"] is None or t_date > nodes[v]["last_seen"]:
#                 nodes[v]["last_seen"] = t_date

#         # Suspicious transaction flag
#         is_suspicious = amt >= 500000

#         # MultiDiGraph preserves multiple transactions
#         G.add_edge(
#             u,
#             v,
#             txn_id=t.id,
#             amount=amt,
#             weight=amt,
#             date=str(t_date) if t_date else None,
#             description=t.description,
#             type=t.type,
#             is_suspicious=is_suspicious
#         )

#     # Add node attributes
#     for node_id, attrs in nodes.items():

#         if attrs["first_seen"]:
#             attrs["first_seen"] = str(attrs["first_seen"])

#         if attrs["last_seen"]:
#             attrs["last_seen"] = str(attrs["last_seen"])

#         G.add_node(node_id, **attrs)

#     return G


# def build_multi_statement_graph(case_id: str) -> nx.MultiDiGraph:
#     """
#     Build graph from all transactions in a case.
#     """
#     transactions = Transaction.query.filter_by(
#         case_id=case_id,
#         is_failed=False
#     ).all()

#     return build_graph(transactions)


# def graph_to_json(G):
#     """
#     Convert graph to JSON serializable format.
#     """
#     from networkx.readwrite import json_graph

#     return json_graph.node_link_data(G)

import networkx as nx
from app.models.transaction import Transaction


# ============================================================================
# GRAPH BUILDER
# ============================================================================

def build_graph(transactions: list) -> nx.MultiDiGraph:
    """
    Build a transaction graph.
    """
    G = nx.MultiDiGraph()
    nodes = {}
    
    # We will track edge signatures to avoid duplicate reconciliation across statements
    # signature: (u, v, date_str, amount_str)
    seen_edges = set()

    for t in transactions:
        # --------------------------------------------------------------
        # FILTER NON-TRANSFER EVENTS
        # --------------------------------------------------------------
        desc = (t.description or "").upper()
        if any(bad in desc for bad in ["OPENING BALANCE", "CLOSING BALANCE", "BALANCE B/F", "BALANCE C/F", "B/F", "C/F"]):
            continue
            
        t_type = (t.type or "").lower()
        if t_type not in ["credit", "cr", "debit", "dr"]:
            continue
            
        # --------------------------------------------------------------
        # RESOLVE STATEMENT ACCOUNT
        # --------------------------------------------------------------
        stmt_acc = None
        if t.statement and t.statement.account_number and t.statement.account_number != "PRIMARY_ACCOUNT":
            stmt_acc = t.statement.account_number
        else:
            # Fallback if statement account number is missing. 
            # We must use something unique per statement if account is completely unknown, 
            # but usually parsers should extract it.
            stmt_acc = f"STATEMENT_{t.statement.id}" if t.statement else "UNKNOWN_STATEMENT"
            
        if not stmt_acc:
            continue
            
        # --------------------------------------------------------------
        # RESOLVE COUNTERPARTY ACCOUNT
        # --------------------------------------------------------------
        c_party = None
        invalid_accounts = {"PRIMARY_ACCOUNT", "UNKNOWN", "SELF", "OPENING BALANCE"}
        
        # Helper to extract valid account
        def get_valid_acc(acc_str):
            if not acc_str: return None
            if str(acc_str).strip().upper() in invalid_accounts:
                return None
            return acc_str

        # Direction rules
        if t_type in ["debit", "dr"]:
            # Money leaving stmt_acc -> c_party
            u = stmt_acc
            
            c_party = get_valid_acc(t.receiver_account)
            if not c_party:
                alt = get_valid_acc(t.sender_account)
                if alt and alt != stmt_acc:
                    c_party = alt
            v = c_party
        else:
            # Money entering c_party -> stmt_acc
            v = stmt_acc
            
            c_party = get_valid_acc(t.sender_account)
            if not c_party:
                alt = get_valid_acc(t.receiver_account)
                if alt and alt != stmt_acc:
                    c_party = alt
            u = c_party

        if not u or not v:
            continue
            
        if u == v:
            continue

        amount = abs(float(t.amount or 0))
        if amount <= 0:
            continue
            
        txn_date = t.date
        date_str = txn_date.isoformat() if txn_date else None
        
        # --------------------------------------------------------------
        # RECONCILIATION
        # --------------------------------------------------------------
        edge_signature = (u, v, date_str, round(amount, 2))
        if edge_signature in seen_edges:
            continue
        seen_edges.add(edge_signature)

        # --------------------------------------------------------------
        # INITIALIZE NODES
        # --------------------------------------------------------------
        if u not in nodes:
            nodes[u] = {
                "total_received": 0.0,
                "total_sent": 0.0,
                "transaction_count": 0,
                "first_seen": txn_date,
                "last_seen": txn_date,
                "risk_score": 0.0,
                "is_statement_account": (u == stmt_acc)
            }
        elif u == stmt_acc:
            nodes[u]["is_statement_account"] = True

        if v not in nodes:
            nodes[v] = {
                "total_received": 0.0,
                "total_sent": 0.0,
                "transaction_count": 0,
                "first_seen": txn_date,
                "last_seen": txn_date,
                "risk_score": 0.0,
                "is_statement_account": (v == stmt_acc)
            }
        elif v == stmt_acc:
            nodes[v]["is_statement_account"] = True

        # --------------------------------------------------------------
        # UPDATE STATS
        # --------------------------------------------------------------
        nodes[u]["total_sent"] += amount
        nodes[u]["transaction_count"] += 1
        nodes[v]["total_received"] += amount
        nodes[v]["transaction_count"] += 1

        if txn_date:
            for node_id in [u, v]:
                if nodes[node_id]["first_seen"] is None or txn_date < nodes[node_id]["first_seen"]:
                    nodes[node_id]["first_seen"] = txn_date
                if nodes[node_id]["last_seen"] is None or txn_date > nodes[node_id]["last_seen"]:
                    nodes[node_id]["last_seen"] = txn_date

        # --------------------------------------------------------------
        # EDGE ATTRIBUTES & RISK PROPAGATION
        # --------------------------------------------------------------
        is_suspicious = amount >= 500000
        
        # Simple heuristic risk for nodes based on transaction volume/suspicion
        risk_increment = 25.0 if is_suspicious else min(20.0, (amount / 50000.0) * 5.0)
        nodes[u]["risk_score"] = min(95.0, nodes[u]["risk_score"] + risk_increment)
        nodes[v]["risk_score"] = min(95.0, nodes[v]["risk_score"] + risk_increment)

        G.add_edge(
            u,
            v,
            txn_id=t.id,
            amount=amount,
            weight=amount,
            date=date_str,
            description=t.description,
            type=getattr(t, "type", None),
            is_suspicious=is_suspicious,
            statement_id=t.statement_id
        )

    # ========================================================================
    # ADD NODE ATTRIBUTES
    # ========================================================================

    for node_id, attrs in nodes.items():

        if attrs["first_seen"]:

            attrs["first_seen"] = (
                attrs["first_seen"]
                .isoformat()
            )

        if attrs["last_seen"]:

            attrs["last_seen"] = (
                attrs["last_seen"]
                .isoformat()
            )
        print(
            node_id,
            attrs["total_received"],
            attrs["total_sent"],
            attrs["transaction_count"]
        )
        G.add_node(
            node_id,
            **attrs
        )

    return G


# ============================================================================
# CASE GRAPH
# ============================================================================

def build_multi_statement_graph(
    case_id: str
) -> nx.MultiDiGraph:

    transactions = (
        Transaction.query
        .filter_by(
            case_id=case_id,
            is_failed=False
        )
        .all()
    )
    from app.models.case import Case
    case_obj = Case.query.get(case_id)
    
    # Extract statement scores
    statement_scores = {}
    if case_obj:
        for s in case_obj.statements:
            if s.account_number:
                statement_scores[s.account_number] = s.suspicion_score
            elif s.id:
                statement_scores[f"STATEMENT_{s.id}"] = s.suspicion_score

    print("\n===== GRAPH DEBUG =====")

    for t in Transaction.query.filter_by(case_id=case_id).limit(10):
        print(
            t.type,
            t.sender_account,
            t.receiver_account,
            t.description
        )
    print("=======================\n")
    
    G = build_graph(transactions)
    
    for node_id in G.nodes:
        # Give exact statement score to primary nodes
        if node_id in statement_scores:
            G.nodes[node_id]["risk_score"] = statement_scores[node_id]
            
    return G


# ============================================================================
# JSON EXPORT
# ============================================================================

def graph_to_json(G):

    from networkx.readwrite import json_graph

    return json_graph.node_link_data(G)