import os
import sys
from datetime import datetime

sys.path.insert(0, "c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main")

from app import create_app
from app.models.case import Case
from app.graph.graph_builder import build_multi_statement_graph
import json

app = create_app()

def parse_date(dstr):
    try:
        return datetime.fromisoformat(dstr)
    except:
        return datetime.min

def format_duration(minutes):
    if minutes < 60: return f"{minutes} minutes"
    hours = minutes // 60
    if hours < 24: return f"{hours} hours"
    days = hours // 24
    if days < 30: return f"{days} days"
    months = days // 30
    return f"{months} months"

def run_money_trail(case_id, start_account_id):
    graph = build_multi_statement_graph(case_id)
    
    credits = []
    for u, v, key, data in graph.in_edges(start_account_id, keys=True, data=True):
        if data.get('type', '').lower() in ['credit', 'cr']:
            credits.append((u, v, key, data))
            
    credits.sort(key=lambda x: parse_date(x[3].get('date')))
    
    edge_capacity = {}
    for u, v, key, data in graph.edges(keys=True, data=True):
        edge_capacity[(u, v, key)] = float(data.get('weight', 0))
        
    best_trail = None
    
    for _, _, _, credit_data in credits:
        credit_amount = float(credit_data.get('weight', 0))
        if credit_amount <= 0: continue
        
        credit_date = parse_date(credit_data.get('date'))
        
        remaining_credit = credit_amount
        traced_amount = 0
        destinations = []
        
        queue = [(start_account_id, credit_date, remaining_credit, destinations, 0)]
        visited_edges = set()
        
        while queue:
            current_acc, current_time, available_funds, current_branch_list, hop = queue.pop(0)
            if available_funds <= 0 or hop > 10: continue
            if current_acc not in graph.nodes: continue
                
            outgoing_edges = []
            for u, v, key, data in graph.out_edges(current_acc, keys=True, data=True):
                edge_id = (u, v, key)
                if edge_capacity.get(edge_id, 0) <= 0: continue
                edge_date = parse_date(data.get('date'))
                if edge_date >= current_time:
                    outgoing_edges.append((edge_date, u, v, key, data))
                    
            outgoing_edges.sort(key=lambda x: x[0])
            
            for edge_date, u, v, key, data in outgoing_edges:
                if available_funds <= 0: break
                edge_id = (u, v, key)
                avail_edge_cap = edge_capacity.get(edge_id, 0)
                if avail_edge_cap <= 0: continue
                
                matched_amount = min(available_funds, avail_edge_cap)
                available_funds -= matched_amount
                edge_capacity[edge_id] -= matched_amount
                
                if hop == 0: traced_amount += matched_amount
                time_held_mins = int((edge_date - current_time).total_seconds() / 60)
                
                branch_node = {
                    "account": v,
                    "actual_debit_amount": float(data.get('weight', 0)),
                    "attributed_amount": matched_amount,
                    "date": edge_date.isoformat(),
                    "time_held_human": format_duration(time_held_mins),
                    "txn_id": data.get('txn_id'),
                    "hop": hop + 1,
                    "branches": []
                }
                current_branch_list.append(branch_node)
                
                has_statement = any(d.get('statement_id') for _, _, d in graph.in_edges(v, data=True)) or any(d.get('statement_id') for _, _, d in graph.out_edges(v, data=True))
                
                if has_statement:
                    queue.append((v, edge_date, matched_amount, branch_node["branches"], hop + 1))
                    
        coverage = (traced_amount / credit_amount * 100) if credit_amount > 0 else 0
        
        flat_trail = [{"account": start_account_id}]
        for d in destinations: flat_trail.append({"account": d["account"]})
            
        trail_result = {
            "seed_detector": "Money Trail",
            "seed_account": start_account_id,
            "original_credit_amount": credit_amount,
            "suspicious_inflow_amount": credit_amount,
            "traced_amount": traced_amount,
            "attributed_outflow_amount": traced_amount,
            "remaining_amount": credit_amount - traced_amount,
            "trail_coverage": round(coverage, 2),
            "outflow_ratio": round(coverage, 2),
            "start_date": credit_date.isoformat() if credit_date != datetime.min else None,
            "depletion_duration": format_duration(0),
            "destination_count": len(destinations),
            "destinations": destinations,
            "trail": flat_trail
        }
        
        if not best_trail: best_trail = trail_result
            
    print(json.dumps(best_trail, indent=2))

with app.app_context():
    case = Case.query.first()
    if case:
        run_money_trail(case.id, "7342128619")
