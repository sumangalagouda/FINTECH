from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.detection_result import DetectionResult
from app.models.case import Case

from app.routes.graph import get_graph_from_db
from app.detectors.circular_flow import detect_circular_flow
from app.detectors.layering_chain import find_layering_chains
from app.detectors.large_transaction import detect_large_transaction
from app.detectors.dormant_revival import detect_dormant_revival
from app.detectors.beneficiary_burst import detect_beneficiary_burst
from app.detectors.high_risk_time import detect_high_risk_time
from app.detectors.structuring import detect_structuring
from app.detectors.velocity import detect_velocity
from app.detectors.pass_through import detect_pass_through
from app.detectors.cash_cycling import detect_cash_cycling
from app.intelligence.suspicion_score import update_case_suspicion_score

intelligence_bp = Blueprint('intelligence', __name__, url_prefix='/api/intelligence')

def save_detection_result(result, case_id, account_number=None, **kwargs):
    from app.models.transaction import Transaction
    if not result:
        return
        
    def process_result(r):
        dr = DetectionResult(
            case_id=case_id,
            account_number=account_number,
            statement_id=kwargs.get('statement_id'),
            detector_name=r.get("detector"),
            triggered=r.get("triggered", False),
            score=r.get("score", 0),
            reason=r.get("reason"),
            transactions_involved=r.get("transactions_involved", []),
            severity=r.get("severity", "none")
        )
        db.session.add(dr)
        
        # Update associated transactions
        txns_involved = r.get("transactions_involved", [])
        if txns_involved:
            for txn_id in txns_involved:
                txn = Transaction.query.get(txn_id)
                if txn:
                    txn.is_flagged = True
                    # Only upgrade risk_level/score if this detector's score is higher
                    if float(r.get("score", 0)) > float(txn.risk_score or 0):
                        txn.risk_score = float(r.get("score", 0))
                        txn.risk_level = r.get("severity", "low")

    if isinstance(result, list):
        for r in result:
            process_result(r)
    else:
        process_result(result)
        
    db.session.commit()

def run_silent_analysis(case_id):
    """
    Runs all detectors for all accounts in the case.
    """
    from app.models.statement import Statement
    
    # 1. Clear previous DetectionResults for this case to avoid stale data
    DetectionResult.query.filter_by(case_id=case_id).delete(synchronize_session=False)
    db.session.commit()
    
    # 2. Get all statements in this case
    statements = Statement.query.filter_by(case_id=case_id).all()
    
    all_results = []
    
    m3_detectors = [
        detect_large_transaction,
        detect_dormant_revival,
        detect_beneficiary_burst,
        detect_high_risk_time,
        detect_structuring
    ]
    
    m4_detectors = [
        detect_velocity,
        detect_pass_through,
        detect_cash_cycling
    ]
    
    # 3. Run STATEMENT-SCOPED detectors
    for statement in statements:
        stmt_results = []
        for detector in m3_detectors + m4_detectors:
            try:
                res = detector(case_id, statement_id=statement.id)
                save_detection_result(res, case_id, statement_id=statement.id)
                if isinstance(res, list):
                    stmt_results.extend(res)
                elif res:
                    stmt_results.append(res)
            except Exception as e:
                print(f"Error in {detector.__name__} for statement {statement.id}: {e}")
                
        # Calculate score for this statement
        score_data = update_case_suspicion_score(case_id, stmt_results, statement_id=statement.id)
        statement.suspicion_score = score_data.get("risk_score", 0)
        statement.severity = score_data.get("risk_level", "low").lower()
        statement.risk_level = score_data.get("risk_level", "low")
        all_results.extend(stmt_results)
        
    db.session.commit()
        
    # 5. Run CASE-SCOPED Graph Intelligence
    graph = get_graph_from_db(case_id)
    
    try:
        cf_results = detect_circular_flow(graph)
        save_detection_result(cf_results, case_id, account_number=None)
        all_results.extend(cf_results)
    except Exception as e:
        print(f"Error in CircularFlow: {e}")
        
    try:
        lc_results = find_layering_chains(graph)
        save_detection_result(lc_results, case_id, account_number=None)
        all_results.extend(lc_results)
    except Exception as e:
        print(f"Error in LayeringChain: {e}")
        
    # Optional AI Summary
    try:
        import threading
        from app.routes.cases import generate_ai_summary_for_case
        from flask import current_app
        
        app = current_app._get_current_object()
        def bg_generate():
            with app.app_context():
                generate_ai_summary_for_case(case_id, force=True)
                
        threading.Thread(target=bg_generate, daemon=True).start()
    except Exception as e:
        print(f"Error triggering AI summary: {e}")
        
    try:
        update_case_suspicion_score(case_id, statement_id=None)
    except Exception as e:
        print(f"Error updating overall case suspicion score: {e}")
        
    return all_results
@intelligence_bp.route('/run-silent', methods=['POST'])
@jwt_required()
def run_silent_endpoint():
    data = request.get_json(silent=True) or {}
    case_id = data.get('case_id')
    if not case_id:
        return jsonify({"error": "case_id is required"}), 400
        
    results = run_silent_analysis(case_id)
    return jsonify({"status": "success", "detectors_run": len(results)})

@intelligence_bp.route('/fifo-trace', methods=['POST'])
@jwt_required()
def fifo_trace_endpoint():
    from app.models.transaction import Transaction
    from app.intelligence.fifo_tracker import fifo_trace_funds
    
    data = request.get_json(silent=True) or {}
    account_id = data.get('account_id')
    case_id = data.get('case_id')
    
    if not account_id or not case_id:
        return jsonify({"error": "account_id and case_id are required"}), 400
        
    # Get all transactions for this case involving this account
    transactions = Transaction.query.filter(
        Transaction.case_id == case_id,
        db.or_(
            Transaction.sender_account == account_id,
            Transaction.receiver_account == account_id
        )
    ).all()
    
    traced_outflows = fifo_trace_funds(account_id, transactions)
    
    return jsonify({
        "account_id": account_id,
        "traced_outflows": traced_outflows
    })
