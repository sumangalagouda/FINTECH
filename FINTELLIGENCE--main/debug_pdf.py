import os
import pdfplumber
import pandas as pd
from typing import List, Optional

def _dataframe_from_pdf(path: str) -> pd.DataFrame:
    header_cols = None
    all_rows: List[List] = []
    
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                page_tables = page.extract_tables()
            except Exception:
                continue
            if not page_tables:
                continue
            for table in page_tables:
                if not table or len(table) < 2:
                    continue
                header_row = table[0]
                header_low = ' '.join([str(h).lower() if h else '' for h in header_row])
                is_txn_header = any(k in header_low for k in ['date', 'value date', 'description', 'narration', 'withdrawal', 'deposit', 'debit', 'credit', 'balance'])
                if is_txn_header:
                    if header_cols is None:
                        header_cols = header_row
                    all_rows.extend(table[1:])
                elif header_cols is not None:
                    if len(table[0]) == len(header_cols):
                        all_rows.extend(table)
                    else:
                        for row in table:
                            if len(row) == len(header_cols):
                                all_rows.append(row)
    if header_cols is None or not all_rows:
        return pd.DataFrame()
    return pd.DataFrame(all_rows, columns=header_cols)

upload_dir = os.path.join("c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main", "uploads", "evidence")
case_id = "2acd7912-d503-47f2-b19c-68a3794632b9"
pdf_file = os.path.join(upload_dir, case_id, "bank_statement_case86_2.pdf")

df = _dataframe_from_pdf(pdf_file)
print("Shape:", df.shape)
if not df.empty:
    print("Columns:", list(df.columns))
    print(df.head(2))
