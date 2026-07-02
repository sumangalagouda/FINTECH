import os
import io
import time
from datetime import datetime
from flask import Blueprint, jsonify, send_file, current_app, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from markupsafe import Markup
import re

from app.models.case import Case
from app.models.transaction import Transaction
from app.models.detection_result import DetectionResult
from app.models.investigator_note import InvestigatorNote
from app.models.user import User
from app.models.evidence_item import EvidenceItem
from app.extensions import db
from app.ai.ollama_client import call_ollama as query_groq

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

def add_watermark(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 60)
    canvas.setFillGray(0.5, 0.2)
    canvas.translate(300, 400)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "CONFIDENTIAL")
    canvas.restoreState()

def simple_markdown_to_html(text):
    if not text:
        return ""
    # Headers
    text = re.sub(r'^### (.*)', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*)', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*)', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Lists
    text = re.sub(r'^\s*-\s+(.*)', r'<li>\1</li>', text, flags=re.MULTILINE)
    # Newlines
    text = text.replace('\n', '<br/>')
    return Markup(text)

@reports_bp.route('/generate/<case_id>', methods=['GET'])
@jwt_required()
def generate_pdf_report(case_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    case = Case.query.get(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404

    # Get Case details
    account_holder = "Unknown"
    account_number = "Unknown"
    bank_name = "Unknown"
    statement_period = "Unknown"
    
    if case.statements:
        s = case.statements[0]
        account_holder = s.account_holder or account_holder
        account_number = s.account_number or account_number
        bank_name = s.bank_name or bank_name
        if s.statement_period_start and s.statement_period_end:
            statement_period = f"{s.statement_period_start.strftime('%d %b %Y')} - {s.statement_period_end.strftime('%d %b %Y')}"

    # Get Detectors
    detectors = DetectionResult.query.filter_by(case_id=case_id).all()
    
    # Get Transactions
    txns = Transaction.query.filter_by(case_id=case_id).order_by(Transaction.date.desc()).all()
    top_transactions = [t for t in txns if t.is_flagged][:10]
    if not top_transactions:
        top_transactions = txns[:5]
        
    max_amount = max([float(t.amount) for t in top_transactions]) if top_transactions else 1
        
    total_debited = sum(float(t.amount) for t in txns if t.type == 'debit')
    
    # Get Investigator Notes
    notes = InvestigatorNote.query.filter_by(case_id=case_id).order_by(InvestigatorNote.created_at.desc()).all()

    # Generate or Retrieve AI Summary
    from app.routes.cases import generate_ai_summary_for_case
    
    summary_text = case.ai_summary
    if not summary_text:
        # Generate it synchronously using the optimized shared function
        summary_text = generate_ai_summary_for_case(case_id, force=False)
        
    if not summary_text:
        summary_text = "Analysis indicates multi-layered movement of funds. AI summary unavailable."

    # Calculate Confidence and Evidence Score
    confidence = min(100, max(50, 60 + round(case.suspicion_score or 0)))
    evidence_score = min(100, max(40, 50 + round((case.suspicion_score or 0) * 0.5)))

    rendered_html = render_template(
        'investigation_report.html',
        investigator_id=f"INV-{datetime.now().year}-{user.id if user else '0000'}",
        case_display_id=case.display_id or f"{case.id[:8]}",
        account_holder=account_holder,
        account_number=account_number,
        bank_name=bank_name,
        statement_period=statement_period,
        severity=case.severity or 'High',
        suspicion_score=round(case.suspicion_score or 0),
        evidence_score=evidence_score,
        confidence=confidence,
        ai_summary=simple_markdown_to_html(summary_text),
        detectors=detectors,
        top_transactions=top_transactions,
        max_amount=max_amount,
        total_debited=total_debited,
        investigator_notes=notes,
        investigator_name=user.name if user else "Investigator",
        today_date=datetime.now().strftime("%d %b %Y")
    )

    # Try to generate PDF using WeasyPrint, fallback to HTML if GTK3 is missing on Windows
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=rendered_html).write_pdf()
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        evidence_dir = os.path.join(upload_folder, 'evidence', case_id)
        os.makedirs(evidence_dir, exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"report_{case_id}_{timestamp}.pdf"
        pdf_path = os.path.join(evidence_dir, filename)
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
            
        evidence = EvidenceItem(
            case_id=case_id,
            item_type="report",
            file_path=pdf_path,
            uploaded_by=current_user_id,
            note_text="Automatically generated Case Summary Report (New Format)"
        )
        db.session.add(evidence)
        db.session.commit()

        return send_file(
            io.BytesIO(pdf_bytes),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        # Fallback to HTML if WeasyPrint fails (e.g. missing gobject on Windows)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        evidence_dir = os.path.join(upload_folder, 'evidence', case_id)
        os.makedirs(evidence_dir, exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"report_{case_id}_{timestamp}.html"
        html_path = os.path.join(evidence_dir, filename)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)
            
        evidence = EvidenceItem(
            case_id=case_id,
            item_type="report",
            file_path=html_path,
            uploaded_by=current_user_id,
            note_text="Automatically generated Case Summary Report (HTML Fallback)"
        )
        db.session.add(evidence)
        db.session.commit()

        # Add a print script to the HTML so it prompts the user to save as PDF
        print_script = "<script>window.onload = function() { window.print(); }</script>"
        printable_html = rendered_html.replace("</body>", f"{print_script}</body>")

        return send_file(
            io.BytesIO(printable_html.encode('utf-8')),
            as_attachment=True,
            download_name=filename,
            mimetype='text/html'
        )
