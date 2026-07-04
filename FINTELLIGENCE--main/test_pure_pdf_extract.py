import os
import sys

# Add app to path
sys.path.insert(0, "c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main")

# We only want to test the PDF parser, we don't need DB or Flask app context
# because statement_extractor.py is just a pure function that returns a dict.
from app.parsers.statement_extractor import extract_statement

upload_dir = os.path.join("c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main", "uploads", "evidence")
case_id = "2acd7912-d503-47f2-b19c-68a3794632b9"
case_folder = os.path.join(upload_dir, case_id)

if os.path.exists(case_folder):
    for file in sorted(os.listdir(case_folder)):
        if file.endswith('.pdf'):
            file_path = os.path.join(case_folder, file)
            print(f"\n=========================================")
            print(f"Testing extraction for {file}")
            print(f"=========================================")
            try:
                data = extract_statement(file_path)
                txns = data.get('transactions', [])
                print(f"Extracted {len(txns)} transactions.")
            except Exception as e:
                print(f"Error extracting: {e}")
