import pdfplumber
import sys

def analyze(path):
    print(f"Analyzing {path}")
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            print(f"Page {i+1}: {len(tables)} tables")
            for j, table in enumerate(tables):
                if not table: continue
                print(f"  Table {j+1}: {len(table)} rows")
                if len(table) > 0:
                    print(f"    Header: {table[0]}")

if __name__ == "__main__":
    analyze("uploads/evidence/abe10270-69f0-49b8-a2cf-f866046f17c9/bank_statement_case94.pdf")
    analyze("uploads/evidence/abe10270-69f0-49b8-a2cf-f866046f17c9/bank_statement_case94_2.pdf")
