import os
from dotenv import load_dotenv
load_dotenv('.env')
import json
from app import create_app
from app.models.case import Case
from app.graph.graph_builder import build_multi_statement_graph
from app.detectors.layering_chain import find_layering_chains

app = create_app()
with app.app_context():
    case = Case.query.first()
    if not case:
        print('No case found')
    else:
        graph = build_multi_statement_graph(case.id)
        chains = find_layering_chains(graph)
        print(f'Valid chains detected: {len(chains)}')
        
        for i, c in enumerate(chains):
            print(f'\nChain {i+1}:')
            print(f'Hop count: {c["metadata"]["hop_count"]}')
            print(f'Nodes: {c["metadata"]["chain"]}')
            print(f'Transactions Involved: {c["transactions_involved"]}')
            print(f'Amount: {c["metadata"]["amount"]}')
