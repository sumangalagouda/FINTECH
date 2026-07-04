import os
from app.parsers.statement_extractor import extract_statement
from app.app import create_app

app = create_app()

upload_dir = os.path.join("c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main", "uploads")
case_id = "2acd7912-d503-47f2-b19c-68a3794632b9"
case_folder = os.path.join(upload_dir, case_id)

with app.app_context():
    if os.path.exists(case_folder):
        for file in os.listdir(case_folder):
            if file.endswith('.pdf'):
                file_path = os.path.join(case_folder, file)
                print(f"\n--- Extracting {file} ---")
                data = extract_statement(file_path)
                txns = data.get('transactions', [])
                print(f"Extracted {len(txns)} transactions")
                if len(txns) < 5:
                    print(txns)
