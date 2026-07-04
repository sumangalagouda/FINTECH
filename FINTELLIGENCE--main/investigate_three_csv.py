import psycopg2
import json

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

# Find cases with multiple statements (specifically the 3 CSV one)
cur.execute("""
    SELECT c.id, c.title, COUNT(s.id) as stmt_count
    FROM cases c
    JOIN statements s ON c.id = s.case_id
    GROUP BY c.id, c.title
    HAVING COUNT(s.id) = 3
""")
cases = cur.fetchall()
print(f"Cases with 3 statements: {cases}")

if cases:
    case_id = cases[0][0]
    print(f"\nAnalyzing Case: {cases[0][1]} ({case_id})")
    
    cur.execute("SELECT id, filename, account_number FROM statements WHERE case_id = %s", (case_id,))
    statements = cur.fetchall()
    
    stmt_map = {}
    print("\nSTATEMENTS:")
    for s in statements:
        print(f"Statement ID: {s[0]} | File: {s[1]} | Account: {s[2]}")
        stmt_map[s[0]] = s
        
    cur.execute("""
        SELECT id, statement_id, type, amount, date, description, sender_account, receiver_account
        FROM transactions 
        WHERE case_id = %s
        ORDER BY date ASC
    """, (case_id,))
    txns = cur.fetchall()
    
    print(f"\nTRANSACTIONS (Total {len(txns)}):")
    for t in txns:
        print(f"[{t[4]}] {t[2].upper()} {t[3]} | Src: {t[6]} | Dst: {t[7]} | Desc: {t[5][:30]}")

conn.close()
