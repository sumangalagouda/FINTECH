from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.case import Case
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.detection_result import DetectionResult


dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/overview', methods=['GET'])
@jwt_required()
def overview():
    # Current DB schema doesn’t include organization on cases/users yet.
    # We implement additive, best-effort overview across all cases for the authenticated user
    # based on Case.created_by/assigned_to.
    user_id = get_jwt_identity()

    visible_cases_q = Case.query.filter((Case.created_by == user_id) | (Case.assigned_to == user_id))

    visible_case_ids = [c.id for c in visible_cases_q.with_entities(Case.id).all()]
    if not visible_case_ids:
        return jsonify({
            "total_statements": 0,
            "total_transactions": 0,
            "high_risk_cases": 0,
            "aml_alerts": 0
        }), 200

    total_statements = db.session.query(db.func.count(Statement.id)).filter(Statement.case_id.in_(visible_case_ids)).scalar() or 0
    total_transactions = db.session.query(db.func.count(Transaction.id)).filter(Transaction.case_id.in_(visible_case_ids)).scalar() or 0

    high_risk_cases = db.session.query(db.func.count(Case.id)).filter(
        Case.id.in_(visible_case_ids),
        Case.risk_level.in_(['high', 'critical'])
    ).scalar() or 0

    aml_alerts = db.session.query(db.func.count(DetectionResult.id)).filter(
        DetectionResult.case_id.in_(visible_case_ids),
        DetectionResult.triggered.is_(True)
    ).scalar() or 0

    return jsonify({
        "total_statements": int(total_statements),
        "total_transactions": int(total_transactions),
        "high_risk_cases": int(high_risk_cases),
        "aml_alerts": int(aml_alerts)
    }), 200

