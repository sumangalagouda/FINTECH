import os
import sys

# Setup minimal app context
from app.app import create_app
from app.detectors.structuring import detect_structuring
from app.models.case import Case
from app.models.statement import Statement

app = create_app()
with app.app_context():
    case_id = 'c9408e25-19b9-4ef5-b750-7678c63f981d'
    # Find statements
    statements = Statement.query.filter_by(case_id=case_id).all()
    for s in statements:
        print(f"Statement: {s.id}")
        res = detect_structuring(case_id, statement_id=s.id)
        print(f"Structuring Results: {res}")
