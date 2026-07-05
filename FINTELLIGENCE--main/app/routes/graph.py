from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.models.case_graph import CaseGraph
from app.graph.graph_builder import build_multi_statement_graph, graph_to_json
from app.detectors.circular_flow import detect_circular_flow
from app.detectors.layering_chain import find_layering_chains
from app.detectors.layering_severity import score_layering_chain
from app.graph.trail_reconstruction import reconstruct_trail
from app.graph.cross_analysis import perform_cross_analysis
from app.graph.relationship_discovery import discover_relationships
from app.extensions import db
import networkx as nx
from networkx.readwrite import json_graph

graph_bp = Blueprint('graph', __name__, url_prefix='/api')

def get_graph_from_db(case_id):
    # Always rebuild to ensure the latest graph builder logic is used
    G = build_multi_statement_graph(case_id)
    
    # Update cache while we're at it
    data = graph_to_json(G)
    cg = CaseGraph.query.filter_by(case_id=case_id).first()
    if cg:
        cg.graph_data = data
    else:
        cg = CaseGraph(case_id=case_id, graph_data=data)
        db.session.add(cg)
    db.session.commit()
    
    return G

@graph_bp.route('/graph/build/<case_id>', methods=['POST'])
@jwt_required()
def build_graph_endpoint(case_id):
    G = build_multi_statement_graph(case_id)
    data = graph_to_json(G)
    
    cg = CaseGraph.query.filter_by(case_id=case_id).first()
    if not cg:
        cg = CaseGraph(case_id=case_id, graph_data=data)
        db.session.add(cg)
    else:
        cg.graph_data = data
    db.session.commit()
    
    return jsonify({"status": "success", "nodes_count": len(G.nodes), "edges_count": len(G.edges)})

@graph_bp.route('/graph/<case_id>', methods=['GET'])
def get_graph(case_id):
    G = build_multi_statement_graph(case_id)
    data = graph_to_json(G)
    
    # Update cache
    cg = CaseGraph.query.filter_by(case_id=case_id).first()
    if cg:
        cg.graph_data = data
    else:
        cg = CaseGraph(case_id=case_id, graph_data=data)
        db.session.add(cg)
    db.session.commit()
    
    return jsonify(data)

@graph_bp.route('/graph/reconstruct-trail', methods=['POST'])
def reconstruct_trail_endpoint():
    data = request.get_json(silent=True) or {}
    case_id = data.get('case_id')
    txn_id = data.get('txn_id')
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
    G = get_graph_from_db(case_id)
    result = reconstruct_trail(G, case_id, txn_id)
    return jsonify(result)

@graph_bp.route('/graph/credit-transactions/<case_id>', methods=['GET'])
def get_credit_transactions(case_id):
    from app.models.transaction import Transaction
    txns = Transaction.query.filter_by(case_id=case_id).all()
    credits = [t for t in txns if t.type.lower() in ['credit', 'cr']]
    credits.sort(key=lambda x: x.date)
    
    result = []
    for t in credits:
        # Determine statement account if receiver is missing/generic
        stmt_acc = t.receiver_account
        if not stmt_acc or stmt_acc == "PRIMARY_ACCOUNT":
            if t.statement and t.statement.account_number:
                stmt_acc = t.statement.account_number
            elif t.statement:
                stmt_acc = f"STATEMENT_{t.statement.id}"
                
        result.append({
            "id": t.id,
            "date": t.date.isoformat(),
            "amount": t.amount,
            "sender_account": t.sender_account or "Unknown Source",
            "receiver_account": stmt_acc or "Primary Account"
        })
        
    return jsonify(result)

@graph_bp.route('/graph/cross-analysis', methods=['POST'])
@jwt_required()
def cross_analysis_endpoint():
    data = request.get_json(silent=True) or {}
    case_id = data.get('case_id')
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
    G = get_graph_from_db(case_id)
    result = perform_cross_analysis(case_id, G)
    return jsonify(result)

@graph_bp.route('/graph/relationships', methods=['POST'])
@jwt_required()
def relationships_endpoint():
    data = request.get_json(silent=True) or {}
    case_id = data.get('case_id')
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
    G = get_graph_from_db(case_id)
    result = discover_relationships(G)
    return jsonify(result)

@graph_bp.route('/detect/circular-flow', methods=['POST'])
@jwt_required()
def detect_circular_flow_endpoint():
    data = request.get_json(silent=True) or {}
    case_id = data.get('case_id')
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
    G = get_graph_from_db(case_id)
    
    results = detect_circular_flow(G)
    return jsonify(results)

@graph_bp.route('/detect/layering-chain', methods=['POST'])
@jwt_required()
def detect_layering_chain_endpoint():
    data = request.get_json(silent=True) or {}
    case_id = data.get('case_id')
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
    G = get_graph_from_db(case_id)
    results = find_layering_chains(G)
    return jsonify(results)

@graph_bp.route('/detect/layering-severity', methods=['POST'])
@jwt_required()
def detect_layering_severity_endpoint():
    data = request.get_json(silent=True) or {}
    case_id = data.get('case_id')
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
    chain = data.get('chain', [])
    # In real scenario we process passed chain. For now we just mock.
    if not chain:
        return jsonify({"error": "No chain provided"}), 400
        
    chain_data = {"chain": chain, "chain_length": len(chain)-1}
    G = get_graph_from_db(case_id)
    result = score_layering_chain(chain_data, G)
    return jsonify(result)
