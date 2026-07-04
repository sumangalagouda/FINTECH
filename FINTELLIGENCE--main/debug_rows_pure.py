import os
import pandas as pd
import pdfplumber
import re
from typing import List, Optional

def _find_column(df_cols, candidates):
    cols = [str(c).strip().lower() for c in df_cols]
    for cand in candidates:
        for i, c in enumerate(cols):
            if cand in c:
                return df_cols[i]
    return None

def _dataframe_from_pdf(path: str) -> pd.DataFrame:
    header_cols = None
    all_rows: List[List] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2: continue
                header_row = table[0]
                header_low = ' '.join([str(h).lower() if h else '' for h in header_row])
                is_txn_header = any(k in header_low for k in ['date', 'value date', 'description', 'narration', 'withdrawal', 'deposit', 'debit', 'credit', 'balance'])
                if is_txn_header:
                    if header_cols is None: header_cols = header_row
                    all_rows.extend(table[1:])
                elif header_cols is not None:
                    if len(table[0]) == len(header_cols):
                        all_rows.extend(table)
                    else:
                        for row in table:
                            if len(row) == len(header_cols):
                                all_rows.append(row)
    if header_cols is None or not all_rows: return pd.DataFrame()
    return pd.DataFrame(all_rows, columns=header_cols)

def _rows_from_dataframe(df: pd.DataFrame) -> List[dict]:
    if df.empty: return []
    cols = list(df.columns)
    date_col = _find_column(cols, ['txn date', 'transaction date', 'date', 'tran date'])
    desc_col = _find_column(cols, ['description', 'narration', 'particulars', 'remarks', 'details'])
    print(f"Date Col: {date_col}, Desc Col: {desc_col}")
    rows = []
    for _idx, r in df.iterrows():
        row = r.to_dict()
        date = row.get(date_col) if date_col else None
        desc = row.get(desc_col, '') if desc_col else ''
        rows.append({'date': date, 'desc': desc})
    return rows

pdf_file = "c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main\\uploads\\evidence\\2acd7912-d503-47f2-b19c-68a3794632b9\\bank_statement_case86_2.pdf"
df = _dataframe_from_pdf(pdf_file)
rows = _rows_from_dataframe(df)
print(f"Total rows: {len(rows)}")
valid_txns = [t for t in rows if t.get('date') or t.get('desc')]
print(f"Valid txns: {len(valid_txns)}")
