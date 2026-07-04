import os

# Refactor silent_engine.py
with open("app/intelligence/silent_engine.py", "r") as f:
    content = f.read()

content = content.replace("def save_detection_result(result, case_id, account_number=None):", "def save_detection_result(result, case_id, account_number=None, statement_id=None):")
content = content.replace("account_number=account_number,", "account_number=account_number,\n            statement_id=statement_id,")

content = content.replace("def run_silent_analysis(case_id):", "def run_silent_analysis(case_id):")

# I'll just write a script that replaces the entire run_silent_analysis block because the logic change is big.
