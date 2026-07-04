import os
import pdfplumber

upload_dir = os.path.join("c:\\Users\\Sumangala\\Desktop\\Final_project\\FINTELLIGENCE-\\FINTELLIGENCE--main", "uploads", "evidence")
case_id = "2acd7912-d503-47f2-b19c-68a3794632b9"
case_folder = os.path.join(upload_dir, case_id)

if os.path.exists(case_folder):
    for file in os.listdir(case_folder):
        if file.endswith('.pdf'):
            file_path = os.path.join(case_folder, file)
            print(f"\n--- PDF: {file} ---")
            with pdfplumber.open(file_path) as pdf:
                total_tables = 0
                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    total_tables += len(tables)
                    print(f"  Page {i+1}: {len(tables)} tables")
                print(f"Total tables: {total_tables}")
