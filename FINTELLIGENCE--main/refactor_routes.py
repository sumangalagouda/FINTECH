import os

with open("app/routes/detectors.py", "r") as f:
    content = f.read()

# I will replace `case_id = data.get('case_id')` with `case_id = data.get('case_id')\n    statement_id = data.get('statement_id')`
# and `detect_large_transaction(case_id)` with `detect_large_transaction(case_id, statement_id=statement_id)`

content = content.replace("case_id = data.get('case_id')", "case_id = data.get('case_id')\n    statement_id = data.get('statement_id')")
content = content.replace("detect_large_transaction(case_id)", "detect_large_transaction(case_id, statement_id=statement_id)")
content = content.replace("detect_dormant_revival(case_id)", "detect_dormant_revival(case_id, statement_id=statement_id)")
content = content.replace("detect_beneficiary_burst(case_id)", "detect_beneficiary_burst(case_id, statement_id=statement_id)")
content = content.replace("detect_high_risk_time(case_id)", "detect_high_risk_time(case_id, statement_id=statement_id)")
content = content.replace("detect_structuring(case_id)", "detect_structuring(case_id, statement_id=statement_id)")
content = content.replace("detect_pass_through(case_id)", "detect_pass_through(case_id, statement_id=statement_id)")
content = content.replace("detect_velocity(case_id)", "detect_velocity(case_id, statement_id=statement_id)")
content = content.replace("detect_cash_cycling(case_id)", "detect_cash_cycling(case_id, statement_id=statement_id)")

with open("app/routes/detectors.py", "w") as f:
    f.write(content)

print("Updated detectors routes")
