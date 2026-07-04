import os
import sys
import pandas as pd
import pdfplumber
import re

sys.path.insert(0, "c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main")
from app.parsers.statement_extractor import _dataframe_from_pdf, _rows_from_dataframe, extract_statement

upload_dir = os.path.join("c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main", "uploads", "evidence")
case_id = "2acd7912-d503-47f2-b19c-68a3794632b9"
pdf_file = os.path.join(upload_dir, case_id, "bank_statement_case86_2.pdf")

df = _dataframe_from_pdf(pdf_file)
rows = _rows_from_dataframe(df)

print(f"Extracted {len(rows)} rows from dataframe")
if rows:
    print(rows[0])
else:
    print("No rows returned from _rows_from_dataframe!")
