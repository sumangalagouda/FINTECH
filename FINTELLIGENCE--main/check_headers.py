import os
import sys
import pdfplumber

upload_dir = os.path.join("c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main", "uploads", "evidence")
case_id = "2acd7912-d503-47f2-b19c-68a3794632b9"
case_folder = os.path.join(upload_dir, case_id)

pdf_file = os.path.join(case_folder, "bank_statement_case86_2.pdf")

print("Checking header rows in", pdf_file)
with pdfplumber.open(pdf_file) as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        if not tables: continue
        for t_idx, table in enumerate(tables):
            if not table or len(table) < 2: continue
            header_row = table[0]
            header_low = ' '.join([str(h).lower() if h else '' for h in header_row])
            print(f"Page {i+1} Table {t_idx+1} Header: {header_low}")
            if i > 2:
                break
