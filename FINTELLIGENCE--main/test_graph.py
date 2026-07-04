from app import create_app
from app.graph.graph_builder import build_multi_statement_graph

app = create_app()
with app.app_context():
    # Find a case with multiple statements
    from app.models.case import Case
    case = Case.query.first()
    if case:
        print(f"Building graph for case: {case.id}")
        G = build_multi_statement_graph(case.id)
        print("Graph Nodes:")
        for node, data in G.nodes(data=True):
            print(f"  {node} (received: {data.get('total_received')}, sent: {data.get('total_sent')})")
        print("\nGraph Edges:")
        for u, v, data in G.edges(data=True):
            print(f"  {u} -> {v} | {data.get('amount')} | {data.get('date')}")
    else:
        print("No cases found.")
