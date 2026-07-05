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

def reconstruct_trail(graph: nx.MultiDiGraph, case_id: str, start_txn_id=None):
    """
    Reconstructs the money trail using ONE chronological credit and FIFO branched allocation.
    Graph topology must be: CREDIT_SOURCE -> PRIMARY_ACCOUNT -> DEBIT_DESTINATION.
    """
    from app.models.transaction import Transaction
    from app.models.detection_result import DetectionResult
    
    seed_txn = None
    
    if start_txn_id:
        seed_txn = Transaction.query.get(start_txn_id)
    
    # Fallback logic to pick a valid credit if none explicitly selected
    if not seed_txn:
        for detector in ['Structuring', 'Large Transaction']:
            detection = DetectionResult.query.filter_by(case_id=case_id, detector_name=detector, triggered=True).first()
            if detection and detection.transactions_involved:
                for tid in detection.transactions_involved:
                    txn = Transaction.query.get(tid)
                    if txn and txn.type.lower() in ['credit', 'cr']:
                        if not seed_txn or txn.date < seed_txn.date:
                            seed_txn = txn
            if seed_txn:
                break
                
    if not seed_txn:
        return {
            "seed_detector": "Money Trail",
            "seed_account": "Unknown",
            "suspicious_inflow_amount": 0,
            "attributed_outflow_amount": 0,
            "outflow_ratio": 0,
            "destinations": [],
            "trail": [],
            "trail_links": []
        }

    # Identify Primary Account 
    def get_statement_account(txn):
        if txn.statement and txn.statement.account_number and txn.statement.account_number != "PRIMARY_ACCOUNT":
            return txn.statement.account_number
        if txn.statement:
            return f"STATEMENT_{txn.statement.id}"
        return "Unknown Account"

    primary_account = seed_txn.receiver_account
    if not primary_account or primary_account == "PRIMARY_ACCOUNT":
        primary_account = get_statement_account(seed_txn)
        
    credit_source = seed_txn.sender_account or "Unknown Source"
    credit_amount = float(seed_txn.amount)
    credit_date = seed_txn.date
    
    remaining_credit = credit_amount
    traced_amount = 0
    destinations = []
    trail_links = []
    
    trail_links.append({
        "source": credit_source,
        "target": primary_account,
        "amount": credit_amount,
        "type": "credit",
        "date": credit_date.isoformat(),
        "id": seed_txn.id
    })

    # Find subsequent debits from this account
    txns = Transaction.query.filter_by(case_id=case_id).all()
    
    # Bookkeeping keywords to ignore
    ignore_keywords = ['gst', 'fee', 'atm', 'charge', 'interest', 'b/f', 'c/f', 'opening', 'closing', 'balance', 'sgst', 'cgst', 'igst', 'penalty', 'tax']
    
    eligible_debits = []
    for t in txns:
        if t.type.lower() not in ['debit', 'dr']:
            continue
            
        t_stmt_acc = t.sender_account
        if not t_stmt_acc or t_stmt_acc == "PRIMARY_ACCOUNT":
            t_stmt_acc = get_statement_account(t)
            
        if t_stmt_acc != primary_account:
            continue
            
        if t.date < credit_date:
            continue
            
        # Ignore bookkeeping
        desc = (t.description or "").lower()
        if any(kw in desc for kw in ignore_keywords):
            continue
            
        eligible_debits.append(t)
        
    eligible_debits.sort(key=lambda x: x.date)
    
    dest_aggregation = {}
    
    for debit in eligible_debits:
        if remaining_credit <= 0:
            break
            
        debit_amount = float(debit.amount)
        if debit_amount <= 0:
            continue
            
        attributed_amount = min(remaining_credit, debit_amount)
        remaining_credit -= attributed_amount
        traced_amount += attributed_amount
        
        # Determine clean destination node name
        dest_node = debit.receiver_account
        if not dest_node or dest_node in ["UNKNOWN", "PRIMARY_ACCOUNT"] or dest_node.startswith("STATEMENT_"):
            if debit.description:
                # Attempt to extract a decent name from description (skip generic prefixes like UPI/Transfer to)
                clean_desc = debit.description.upper()
                prefixes = ["UPI/", "UPI-", "TRANSFER TO ", "NEFT TO ", "RTGS TO ", "IMPS TO ", "PAID TO "]
                for p in prefixes:
                    if clean_desc.startswith(p):
                        clean_desc = clean_desc[len(p):]
                if clean_desc.strip():
                    dest_node = clean_desc.strip()[:30] # Limit length
                else:
                    dest_node = "Cash / POS / Withdrawal"
            else:
                dest_node = "Cash / POS / Withdrawal"
                
        if dest_node not in dest_aggregation:
            time_held_mins = int((debit.date - credit_date).total_seconds() / 60)
            dest_aggregation[dest_node] = {
                "account": dest_node,
                "attributed_amount": 0,
                "actual_debit_amount": 0,
                "date": debit.date.isoformat(),
                "time_held_human": format_duration(time_held_mins),
                "txn_id": debit.id,
                "hop": 1,
                "branches": []
            }
            
        dest_aggregation[dest_node]["attributed_amount"] += attributed_amount
        dest_aggregation[dest_node]["actual_debit_amount"] += debit_amount

    for dest_node, agg_data in dest_aggregation.items():
        destinations.append(agg_data)
        trail_links.append({
            "source": primary_account,
            "target": dest_node,
            "amount": agg_data["attributed_amount"],
            "type": "debit",
            "date": agg_data["date"],
            "id": agg_data["txn_id"]
        })
        
    coverage = (traced_amount / credit_amount * 100) if credit_amount > 0 else 0
    
    flat_trail = [{"account": credit_source}, {"account": primary_account}]
    for d in destinations:
        flat_trail.append({"account": d["account"]})
        
    return {
        "seed_detector": "Money Trail",
        "seed_account": credit_source,
        "original_credit_amount": credit_amount,
        "suspicious_inflow_amount": credit_amount,
        "traced_amount": traced_amount,
        "attributed_outflow_amount": traced_amount,
        "remaining_amount": remaining_credit,
        "trail_coverage": round(coverage, 2),
        "outflow_ratio": round(coverage, 2),
        "start_date": credit_date.isoformat(),
        "depletion_duration": format_duration(0),
        "destination_count": len(destinations),
        "destinations": destinations,
        "trail": flat_trail,
        "trail_links": trail_links
    }