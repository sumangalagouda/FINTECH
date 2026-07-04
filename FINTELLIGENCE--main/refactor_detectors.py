import os
import glob

detectors = [
    "velocity.py", "pass_through.py", "structuring.py", 
    "large_transaction.py", "high_risk_time.py", 
    "dormant_revival.py", "cash_cycling.py", "beneficiary_burst.py"
]

for d in detectors:
    path = os.path.join("app/detectors", d)
    with open(path, "r") as f:
        content = f.read()
    
    # Replace function signature
    content = content.replace("account_number: str = None", "statement_id: str = None")
    
    # Replace query filter
    # Currently it looks like:
    # .join(Statement)
    # .filter(Transaction.case_id == case_id, Transaction.is_failed == False)
    # if account_number:
    #    query = query.filter(Statement.account_number == account_number)
    
    # We will replace account_number with statement_id
    content = content.replace("if account_number:", "if statement_id:")
    content = content.replace("query.filter(Statement.account_number == account_number)", "query.filter(Transaction.statement_id == statement_id)")
    
    with open(path, "w") as f:
        f.write(content)
        
print("Updated all detectors.")
