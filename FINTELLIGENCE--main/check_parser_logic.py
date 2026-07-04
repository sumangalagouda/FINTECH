import os
import sys
import pandas as pd
sys.path.insert(0, "c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main")

from app.parsers.statement_extractor import extract_statement, _dataframe_from_pdf, _normalize_dataframe

upload_dir = os.path.join("c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main", "uploads", "evidence")
case_id = "2acd7912-d503-47f2-b19c-68a3794632b9"
case_folder = os.path.join(upload_dir, case_id)

files = ["bank_statement_case86.pdf", "bank_statement_case86_2.pdf", "bank_statement_case86_3.pdf"]

for f in files:
    f_path = os.path.join(case_folder, f)
    print(f"\n==== {f} ====")
    try:
        df_raw = _dataframe_from_pdf(f_path)
        print(f"Raw DataFrame shape: {df_raw.shape}")
        if not df_raw.empty:
            print(f"Raw Columns: {list(df_raw.columns)}")
            txns = extract_statement(f_path).get('transactions', [])
            print(f"Normalized Transactions length: {len(txns)}")
            if len(txns) < 3:
                print("First few txns:", txns)
    except Exception as e:
        print(f"Error: {e}")
