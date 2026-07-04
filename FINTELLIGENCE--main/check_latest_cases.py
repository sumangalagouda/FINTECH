import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("""
    SELECT c.id, c.title
    FROM cases c
    ORDER BY c.created_at DESC
    LIMIT 3
""")
cases = cur.fetchall()

for case in cases:
    print(f"\nCase: {case[1]} (ID: {case[0]})")
    cur.execute("""
        SELECT s.id, s.filename, s.account_number, s.suspicion_score,
               (SELECT COUNT(*) FROM transactions WHERE statement_id = s.id) as txn_count
        FROM statements s
        WHERE s.case_id = %s
        ORDER BY s.created_at ASC
    """, (case[0],))
    stmts = cur.fetchall()
    for s in stmts:
        print(f"  Statement: {s[1]} | Account: {s[2]} | Score: {s[3]} | Txns: {s[4]}")

conn.close()
