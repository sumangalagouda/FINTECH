import os
import sys
import pandas as pd
import pdfplumber
import re

sys.path.insert(0, "c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main")

from app.parsers.statement_extractor import _dataframe_from_pdf, _rows_from_dataframe, extract_statement

f_path = sys.argv[1]
print(f"\n==== {f_path} ====")
try:
    df_raw = _dataframe_from_pdf(f_path)
    print(f"Raw DataFrame shape: {df_raw.shape}")
    if not df_raw.empty:
        print(f"Raw Columns: {list(df_raw.columns)}")
        rows = _rows_from_dataframe(df_raw)
        print(f"Rows extracted: {len(rows)}")
        if rows:
            print("First row:", rows[0])
    
    extracted = extract_statement(f_path)
    print(f"Extracted transactions: {len(extracted.get('transactions', []))}")
except Exception as e:
    import traceback
    traceback.print_exc()
