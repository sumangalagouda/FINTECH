import sys
import os
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

load_dotenv()

from app import create_app
from app.extensions import db
from app.models.case import Case
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.detection_result import DetectionResult

app = create_app()

with app.app_context():
    c = Case.query.order_by(Case.created_at.desc()).first()
    print(f"Case ID: {c.id}")
    print(f"Title: {c.title}")
    print(f"Case Score: {c.suspicion_score}")
    
    statements = Statement.query.filter_by(case_id=c.id).order_by(Statement.created_at).all()
    print("Transactions per statement:")
    for s in statements:
        txns = Transaction.query.filter_by(statement_id=s.id).all()
        debits = sum(t.amount for t in txns if t.type == 'debit')
        credits = sum(t.amount for t in txns if t.type == 'credit')
        print(f"Statement {s.filename}: {len(txns)} transactions, Debits: {debits}, Credits: {credits}, Score: {s.suspicion_score}")
        
    print("\nDetection Results:")
    results = DetectionResult.query.filter_by(case_id=c.id).all()
    for r in results:
        stmt_name = next((s.filename for s in statements if s.id == r.statement_id), "CASE SCOPE")
        print(f"[{stmt_name}] {r.detector_name}: {r.score} (Triggered: {r.triggered})")
