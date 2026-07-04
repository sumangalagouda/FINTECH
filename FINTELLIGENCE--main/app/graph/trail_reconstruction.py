import networkx as nx
from datetime import datetime
from app.models.detection_result import DetectionResult
from app.models.transaction import Transaction

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
        d1 = datetime.strptime(date1, "%Y-%m-%dT%H:%M:%S") if "T" in date1 else datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%dT%H:%M:%S") if "T" in date2 else datetime.strptime(date2, "%Y-%m-%d")
        return int((d2 - d1).total_seconds() / 60)
    except Exception:
        return 0

def reconstruct_trail(graph: nx.MultiDiGraph, case_id: str, start_account_id=None):
    """
    Reconstructs the money trail using Suspicious Inflow seeding and FIFO branched allocation.
    """
    seeds = []
    
    if start_account_id:
        # If explicitly given an account, find its first inflow
        from app.models.transaction import Transaction
        txns = Transaction.query.filter_by(case_id=case_id).all()
        
        def get_statement_account(txn):
            if txn.statement and txn.statement.account_number and txn.statement.account_number != "PRIMARY_ACCOUNT":
                return txn.statement.account_number
            if txn.statement:
                return f"STATEMENT_{txn.statement.id}"
            return None
            
        for txn in sorted(txns, key=lambda t: t.date):
            stmt_acc = get_statement_account(txn)
            if txn.receiver_account == start_account_id or (stmt_acc == start_account_id and txn.type in ['credit', 'cr']):
                seeds.append(txn)
                break
    else:
        # Use Structuring detector output as seeds
        detection = DetectionResult.query.filter_by(
            case_id=case_id, 
            detector_name='Structuring',
            triggered=True
        ).first()
        
        if detection and detection.transactions_involved:
            for tid in detection.transactions_involved:
                txn = Transaction.query.get(tid)
                if txn and txn.type.lower() in ['credit', 'cr']:
                    seeds.append(txn)
                    
        # Fallback to Large Transaction
        if not seeds:
            detection = DetectionResult.query.filter_by(
                case_id=case_id, 
                detector_name='Large Transaction',
                triggered=True
            ).first()
            if detection and detection.transactions_involved:
                for tid in detection.transactions_involved:
                    txn = Transaction.query.get(tid)
                    if txn and txn.type.lower() in ['credit', 'cr']:
                        seeds.append(txn)

    if not seeds:
        return {
            "trail": [],
            "suspicious_inflow_amount": 0,
            "attributed_outflow_amount": 0,
            "outflow_ratio": 0,
            "destinations": []
        }
        
    seeds.sort(key=lambda t: t.date)
    def get_statement_account(txn):
        if txn.statement and txn.statement.account_number and txn.statement.account_number != "PRIMARY_ACCOUNT":
            return txn.statement.account_number
        if txn.statement:
            return f"STATEMENT_{txn.statement.id}"
        return None

    seed_account = seeds[0].receiver_account or get_statement_account(seeds[0])
    if seed_account not in graph.nodes:
        seed_account = get_statement_account(seeds[0])

    if not seed_account or seed_account not in graph.nodes:
        return {
            "trail": [],
            "suspicious_inflow_amount": 0,
            "attributed_outflow_amount": 0,
            "outflow_ratio": 0,
            "destinations": []
        }

    suspicious_inflow_amount = sum(t.amount for t in seeds)
    first_seed_time = seeds[0].date
    last_seed_time = seeds[-1].date
    
    attributed_outflow_amount = 0
    
    # We will build a tree of allocations
    # Queue stores: (current_account, current_time, available_suspicious_funds, current_tree_node, current_hop)
    
    destinations = []
    
    queue = [(seed_account, first_seed_time, suspicious_inflow_amount, destinations, 0)]
    
    visited_edges = set() # (u, v, txn_id)
    all_dest_accounts = set()
    total_minutes = 0
    first_outflow_time = None
    last_outflow_time = None

    while queue:
        current_acc, current_time, available_funds, current_branch_list, hop = queue.pop(0)
        if available_funds <= 0 or hop > 10:
            continue
            
        if current_acc not in graph.nodes:
            continue
            
        # Get all outgoing edges from current_acc
        outgoing_edges = []
        for u, v, key, data in graph.edges(current_acc, keys=True, data=True):
            edge_id = (u, v, data.get('txn_id'))
            if edge_id in visited_edges:
                continue
                
            edge_date_str = data.get('date')
            if not edge_date_str: continue
            
            try:
                edge_date = datetime.fromisoformat(edge_date_str)
            except:
                continue
                
            if edge_date >= current_time:
                outgoing_edges.append((edge_date, u, v, data, edge_id))
                
        # Sort chronologically
        outgoing_edges.sort(key=lambda x: x[0])
        
        for edge_date, u, v, data, edge_id in outgoing_edges:
            if available_funds <= 0:
                break
                
            visited_edges.add(edge_id)
            
            debit_amount = float(data.get('weight', 0))
            if debit_amount <= 0: continue
            
            attributed_amount = min(debit_amount, available_funds)
            available_funds -= attributed_amount
            
            if hop == 0:
                attributed_outflow_amount += attributed_amount
                if not first_outflow_time: first_outflow_time = edge_date
                last_outflow_time = edge_date
                
            all_dest_accounts.add(v)
            
            time_held_mins = int((edge_date - current_time).total_seconds() / 60)
            if hop == 0:
                total_minutes += time_held_mins

            branch_node = {
                "account": v,
                "attributed_amount": attributed_amount,
                "date": edge_date.isoformat(),
                "time_held_human": format_duration(time_held_mins),
                "txn_id": data.get('txn_id'),
                "hop": hop + 1,
                "branches": []
            }
            
            current_branch_list.append(branch_node)
            
            # Continue tracing downstream ONLY if v has a statement in the case
            # We can approximate this by checking if v is a statement account for any transaction in the graph
            has_statement = any(d.get('statement_id') for _, _, d in graph.in_edges(v, data=True)) or any(d.get('statement_id') for _, _, d in graph.out_edges(v, data=True))
            
            if has_statement:
                queue.append((v, edge_date, attributed_amount, branch_node["branches"], hop + 1))

    outflow_ratio = (attributed_outflow_amount / suspicious_inflow_amount * 100) if suspicious_inflow_amount > 0 else 0
    
    # Flatten the tree to a list for 'trail' to keep FundFlowView compatible
    flat_trail = [{"account": seed_account}]
    for d in destinations:
        flat_trail.append({"account": d["account"]})
    
    return {
        "seed_detector": "Structuring",
        "seed_account": seed_account,
        "suspicious_inflow_amount": suspicious_inflow_amount,
        "attributed_outflow_amount": attributed_outflow_amount,
        "outflow_ratio": round(outflow_ratio, 2),
        "depletion_duration": format_duration(total_minutes),
        "destination_count": len(all_dest_accounts),
        "destinations": destinations,
        "trail": flat_trail
    }