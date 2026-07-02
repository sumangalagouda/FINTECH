import os
import time
from flask import send_file, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from app.reports.report_generator import reports_bp
from app.models.case import Case
from app.models.digital_signature import DigitalSignature
from app.models.sio_action import SIOAction
from app.models.evidence_item import EvidenceItem
from app.extensions import db
from app.ai.ollama_client import call_ollama

@reports_bp.route('/closure-memo/<case_id>', methods=['GET', 'POST'])
@jwt_required()
def generate_closure_memo(case_id):
    current_user_id = get_jwt_identity()
    case = Case.query.get(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404

    # Fetch the SIO action/closure decision if any
    sio_action = SIOAction.query.filter_by(case_id=case_id).order_by(SIOAction.created_at.desc()).first()
    signature = DigitalSignature.query.filter_by(case_id=case_id).order_by(DigitalSignature.signed_at.desc()).first()

    system_prompt = (
        "You are an expert financial crime investigator writing an official INVESTIGATION CLOSURE MEMO. "
        "Your task is to write a strictly professional, factual document justifying the closure of a case due to insufficient evidence. "
        "Do NOT hallucinate facts. Only use the provided data. Format the output nicely in plain text, do NOT use markdown formatting (no asterisks, no hash signs)."
    )
    
    user_prompt = f"""
Please generate the INVESTIGATION CLOSURE MEMO based on the following template and case facts.

TEMPLATE:
INVESTIGATION CLOSURE MEMO
Case ID: [Case ID]

1. Case Overview:
   - Account: [Account Number]
   - Initial Trigger: [Why the case was opened]
2. AI Suspicion Metrics:
   - Suspicion Score: [Score]/100
3. Investigation Findings:
   - [Summarize why there is insufficient evidence based on the findings]
4. Conclusion & Directives:
   - Insufficient evidence of financial crime. No regulatory reporting required. Account monitoring returned to standard parameters.
5. Authorization:
   - Closed By: [Sr. IO Name or 'Authorized Officer']
   - Date: [Timestamp]
   - Signature Hash: [Hash]

CASE FACTS:
- Case ID: {case_id}
- Account: {case.bank_name} - {case.account_number}
- Suspicion Score: {case.suspicion_score}
- Risk Level: {case.risk_level}
- SIO Remarks: {sio_action.notes if sio_action else 'No additional remarks provided.'}
- Closed By User ID: {sio_action.user_id if sio_action else current_user_id}
- Signature Hash: {signature.signature_hash if signature else 'N/A'}
"""
    
    try:
        ollama_response = call_ollama(system_prompt, user_prompt, max_tokens=1024)
    except Exception as e:
        ollama_response = f"Failed to generate AI response. Error: {str(e)}\n\nCase ID: {case_id}\nSuspicion Score: {case.suspicion_score}"

    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    evidence_dir = os.path.join(upload_folder, 'evidence', case_id)
    os.makedirs(evidence_dir, exist_ok=True)

    timestamp = int(time.time())
    filename = f"closure_memo_{case_id}_{timestamp}.pdf"
    pdf_path = os.path.join(evidence_dir, filename)

    doc = SimpleDocTemplate(pdf_path)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("INVESTIGATION CLOSURE MEMO", styles["Title"]))
    story.append(Spacer(1, 20))

    for line in ollama_response.split("\n"):
        if line.strip():
            # Basic cleanup of any leftover markdown
            clean_line = line.replace('**', '').replace('##', '')
            story.append(Paragraph(clean_line, styles["BodyText"]))
            story.append(Spacer(1, 6))

    doc.build(story)

    # Log as evidence
    evidence = EvidenceItem(
        case_id=case_id,
        item_type="report",
        file_path=pdf_path,
        uploaded_by=current_user_id,
        note_text="Automatically generated Investigation Closure Memo"
    )
    db.session.add(evidence)
    db.session.commit()

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )
