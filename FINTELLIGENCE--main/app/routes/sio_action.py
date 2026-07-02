import hashlib
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from app.extensions import db
from app.models.user import User
from app.models.case import Case
from app.models.digital_signature import DigitalSignature
from app.models.sio_action import SIOAction
from app.models.verification import Verification
from app.models.detection_result import DetectionResult
from app.models.audit_trail import AuditTrail
from app.intelligence.fir_readiness import calculate_fir_readiness
from app.intelligence.suspicion_score import update_case_suspicion_score

sio_bp = Blueprint('sio_action', __name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_user():
    """Get the current authenticated user from JWT"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)


def get_org_threshold(organization_id=None, default=70):
    """
    Get the suspicion score threshold for an organization.
    Currently returns a default value; can be extended for org-specific config.
    """
    # TODO: Implement org-level threshold configuration
    return default


def get_ipc_suggestions(case_id):
    """
    Auto-suggest IPC sections based on which detectors triggered for this case.
    Returns list of applicable IPC/PMLA sections.
    """
    results = DetectionResult.query.filter_by(
        case_id=case_id,
        triggered=True
    ).all()

    detector_names = [r.detector_name for r in results]
    sections = []

    # Map detectors to IPC sections
    if 'Structuring' in detector_names or 'CashCycling' in detector_names:
        sections.append('PMLA Section 3 — Money Laundering')
    if 'LargeTransaction' in detector_names or 'PassThrough' in detector_names:
        sections.append('IPC 420 — Cheating')
    if 'CircularFlow' in detector_names or 'LayeringChain' in detector_names:
        sections.append('IPC 467 — Forgery of Valuable Security')
    if 'BeneficiaryBurst' in detector_names:
        sections.append('IPC 471 — Using Forged Documents')

    # Default fallback
    if not sections:
        sections = ['IPC 420 — Cheating']

    return sections


def get_submission_recommendation(case_id):
    """
    Auto-suggest submission authority based on case severity and detectors.
    Returns primary recommended authority.
    """
    case = Case.query.get(case_id)
    if not case:
        return 'Economic Offences Wing'

    # Simple heuristic based on risk level and severity
    if case.risk_level == 'CRITICAL' or case.severity == 'critical':
        return 'Central Bureau of Investigation'
    elif case.risk_level == 'HIGH' or case.severity == 'high':
        return 'Enforcement Directorate (ED)'
    else:
        return 'Economic Offences Wing'


def get_success_message(decision):
    """Return outcome message based on Sr. IO's decision"""
    messages = {
        'recommend_fir': (
            'FIR filing recommended. '
            'FIR draft is now available in the Reports tab.'
        ),
        'close_insufficient_evidence': (
            'Case closed. Decision recorded with your digital signature.'
        ),
        'return_to_io': (
            'Case returned to Investigation Officer with your notes.'
        ),
        'escalate_external': (
            'Case escalated to external authority. '
            'Referral letter available in Reports.'
        )
    }
    return messages.get(decision, 'Action recorded.')


def get_case_status_from_decision(decision):
    """Map Sr. IO decision to case status"""
    status_map = {
        'recommend_fir': 'fir_recommended',
        'close_insufficient_evidence': 'closed',
        'return_to_io': 'under_review',
        'escalate_external': 'escalated_external'
    }
    return status_map.get(decision, 'open')


def log_audit_action(case_id, action, performed_by, notes=None, old_value=None, new_value=None):
    """Log action to audit trail"""
    audit = AuditTrail(
        case_id=case_id,
        action=action,
        performed_by=performed_by,
        notes=notes,
        old_value=old_value,
        new_value=new_value,
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()


def notify_io(case_id, decision, remarks):
    """
    Notify the Investigation Officer about the Sr. IO's decision.
    Currently a placeholder for email/notification system integration.
    TODO: Implement actual notification (email, SMS, dashboard notification)
    """
    case = Case.query.get(case_id)
    if not case:
        return

    # Map decision to notification message
    notification_msg = {
        'return_to_io': f'Case {case.display_id} returned for further investigation with remarks: {remarks}',
        'close_insufficient_evidence': f'Case {case.display_id} closed due to insufficient evidence.',
        'recommend_fir': f'Case {case.display_id} recommended for FIR filing.',
        'escalate_external': f'Case {case.display_id} escalated to external authority.'
    }

    msg = notification_msg.get(decision, 'Case decision updated.')
    # TODO: Send email/notification to IO
    print(f"[NOTIFICATION] {msg}")


# ============================================================================
# ENDPOINT 1: GATE CHECK
# ============================================================================

@sio_bp.route('/api/cases/<case_id>/action-gate-check', methods=['GET'])
@jwt_required()
def action_gate_check(case_id):
    """
    Step 1 of the Take Action flow.
    Checks all readiness conditions and returns their status.
    Does NOT block the Sr. IO — just informs.
    
    Returns:
        - Gate conditions (checklist, IO signature, FIR readiness)
        - Suspicion score and threshold comparison
        - Auto-suggested authority and IPC sections
        - Warning if below threshold (for override)
    """
    current_user = get_current_user()

    # Only Sr. IO / Supervisor / Admin can perform this
    if current_user.role not in ['sr_io', 'supervisor', 'admin']:
        return jsonify({
            'error': 'Only Senior Investigation Officers can take action'
        }), 403

    case = Case.query.get(case_id)
    if not case:
        return jsonify({'error': 'Case not found'}), 404

    # Get FIR readiness
    fir_readiness = calculate_fir_readiness(case_id)
    fir_readiness_score = fir_readiness.get('fir_readiness_score', 0)

    # Get suspicion score
    suspicion_data = update_case_suspicion_score(case_id)
    suspicion_score = suspicion_data.get('risk_score', 0)

    # Check IO signature exists
    io_signature = DigitalSignature.query.filter_by(
        case_id=case_id,
        signer_role='io'
    ).first()

    # Check verification checklist
    checklist = Verification.query.filter_by(
        case_id=case_id
    ).first()
    checklist_complete = (
        checklist.completion_percentage == 100
        if checklist else False
    )

    # Determine threshold
    threshold = get_org_threshold(
        default=70
    )

    below_threshold = suspicion_score < threshold

    return jsonify({
        'case_id': case_id,
        'gate_conditions': {
            'checklist_complete': {
                'status': checklist_complete,
                'label': 'Verification Checklist',
                'value': f"{checklist.completion_percentage if checklist else 0}%"
            },
            'io_signed': {
                'status': io_signature is not None,
                'label': 'IO Digital Signature',
                'value': 'Present' if io_signature else 'Missing'
            },
            'fir_readiness': {
                'status': fir_readiness_score >= 50,  # FIR readiness score threshold
                'label': 'FIR Readiness Score',
                'value': f"{fir_readiness_score:.0f}%"
            }
        },
        'suspicion_score': suspicion_score,
        'threshold': threshold,
        'below_threshold': below_threshold,
        'can_proceed': True,
        'warning': (
            f"Suspicion score ({suspicion_score:.1f}) "
            f"is below threshold ({threshold}). "
            f"Proceeding will be flagged as an "
            f"officer override in the audit trail."
            if below_threshold else None
        ),
        'auto_suggested_authority': get_submission_recommendation(case_id),
        'auto_suggested_ipc_sections': get_ipc_suggestions(case_id)
    }), 200


# ============================================================================
# ENDPOINT 2: SUBMIT SR. IO ACTION (with digital signature)
# ============================================================================

@sio_bp.route('/api/cases/<case_id>/sio-action', methods=['POST'])
@jwt_required()
def submit_sio_action(case_id):
    """
    Step 3 of the Take Action flow.
    Sr. IO submits their decision with digital signature (password-verified).
    This is the point of no return — updates case status and creates immutable signature record.
    
    Request JSON:
        {
            "decision": "recommend_fir | close_insufficient_evidence | return_to_io | escalate_external",
            "authority": "Economic Offences Wing",
            "ipc_sections": ["IPC 420", "PMLA Section 3"],
            "remarks": "Sr. IO's reasoning (min 10 chars)",
            "password": "sr_io_password"
        }
    
    Returns:
        - Success status
        - Case status after update
        - Signature hash
        - Override flag
        - FIR draft unlock status
    """
    current_user = get_current_user()

    if current_user.role not in ['sr_io', 'supervisor', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403

    case = Case.query.get(case_id)
    if not case:
        return jsonify({'error': 'Case not found'}), 404

    data = request.get_json() or {}
    decision = data.get('decision')
    authority = data.get('authority')
    ipc_sections = data.get('ipc_sections', [])
    remarks = data.get('remarks', '').strip()
    password = data.get('password')

    # Validate required fields
    if not all([decision, remarks, password]):
        return jsonify({
            'error': 'decision, remarks and password are all required'
        }), 400

    if len(remarks) < 10:
        return jsonify({
            'error': 'Remarks must be at least 10 characters'
        }), 400

    valid_decisions = [
        'recommend_fir',
        'close_insufficient_evidence',
        'return_to_io',
        'escalate_external'
    ]
    if decision not in valid_decisions:
        return jsonify({
            'error': f'Invalid decision. Must be one of: {valid_decisions}'
        }), 400

    # Verify password (re-authenticate before signing)
    if not check_password_hash(current_user.password_hash, password):
        return jsonify({
            'error': 'Incorrect password. Signature not applied.'
        }), 401

    # Get suspicion score at this moment
    suspicion_data = update_case_suspicion_score(case_id)
    suspicion_score = suspicion_data.get('risk_score', 0)
    threshold = get_org_threshold(default=70)

    # Build signature hash
    timestamp_str = datetime.now(timezone.utc).isoformat()
    raw = (
        f"{case_id}{decision}{timestamp_str}"
        f"{str(current_user.id)}"
        f"{current_user.password_hash}"
    )
    signature_hash = hashlib.sha256(raw.encode()).hexdigest()

    # Create digital signature record
    signature = DigitalSignature(
        case_id=case_id,
        signed_by=current_user.id,
        signer_role=current_user.role,
        decision=decision,
        authority=authority,
        ipc_sections=ipc_sections,
        remarks=remarks,
        signature_hash=signature_hash,
        suspicion_score_at_signing=suspicion_score,
        is_override=suspicion_score < threshold,
        signed_at=datetime.now(timezone.utc)
    )
    db.session.add(signature)
    db.session.flush()  # Get the signature ID

    # Create SIO action record
    sio_action = SIOAction(
        case_id=case_id,
        signature_id=signature.id,
        decision=decision,
        authority=authority,
        ipc_sections=ipc_sections,
        remarks=remarks,
        submission_authority=authority,
        created_by=current_user.id,
        notified_io=False
    )
    db.session.add(sio_action)

    # Update case status based on decision
    old_status = case.status
    case.status = get_case_status_from_decision(decision)
    case.sr_io_signature_id = signature.id if hasattr(case, 'sr_io_signature_id') else None

    # Log to audit trail
    log_audit_action(
        case_id=case_id,
        action=f'sio_decision_{decision}',
        performed_by=current_user.id,
        old_value={'status': old_status},
        new_value={'status': case.status},
        notes=(
            f"Sr. IO decision: {decision}. "
            f"Remarks: {remarks}. "
            f"Suspicion score at signing: {suspicion_score:.1f}. "
            f"Override: {suspicion_score < threshold}. "
            f"Authority: {authority}"
        )
    )

    # Notify IO if case returned or closed
    if decision in ['return_to_io', 'close_insufficient_evidence', 'recommend_fir']:
        notify_io(case_id, decision, remarks)
        sio_action.notified_io = True

    db.session.commit()

    return jsonify({
        'status': 'success',
        'decision': decision,
        'case_status': case.status,
        'signature_hash': signature_hash,
        'signed_at': timestamp_str,
        'is_override': suspicion_score < threshold,
        'fir_draft_unlocked': decision == 'recommend_fir',
        'message': get_success_message(decision)
    }), 200


# ============================================================================
# ENDPOINT 3: GET SR. IO DECISION
# ============================================================================

@sio_bp.route('/api/cases/<case_id>/sio-decision', methods=['GET'])
@jwt_required()
def get_sio_decision(case_id):
    """
    Returns the Sr. IO's recorded decision and signature for display.
    Used in Reports tab and case summary.
    
    Returns:
        - Decision details (decision, authority, IPC sections, remarks)
        - Signer info (name, role, signature hash)
        - Timestamp of signing
        - Suspicion score at signing
        - Override status
        - FIR draft unlock status
    """
    # Get latest SIO action for this case
    action = SIOAction.query.filter_by(
        case_id=case_id
    ).order_by(
        SIOAction.created_at.desc()
    ).first()

    if not action:
        return jsonify({'has_action': False}), 200

    signature = DigitalSignature.query.get(action.signature_id)
    if not signature:
        return jsonify({'has_action': False}), 200

    signer = User.query.get(signature.signed_by)

    return jsonify({
        'has_action': True,
        'decision': action.decision,
        'authority': action.authority,
        'ipc_sections': action.ipc_sections,
        'remarks': action.remarks,
        'signed_by_name': signer.name if signer else 'Unknown',
        'signed_by_role': 'Senior Investigation Officer',
        'signature_hash': signature.signature_hash,
        'signed_at': signature.signed_at.isoformat() if signature.signed_at else None,
        'suspicion_score_at_signing': signature.suspicion_score_at_signing,
        'is_override': signature.is_override,
        'fir_draft_unlocked': action.decision == 'recommend_fir'
    }), 200
