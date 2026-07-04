import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("""
    SELECT c.id, c.title
    FROM cases c
    WHERE c.title = 'Investigation: 61577175569879.pdf'
    ORDER BY c.created_at DESC
    LIMIT 1
""")
case = cur.fetchone()

if case:
    print(f"Case ID: {case[0]}")
    cur.execute("""
        SELECT statement_id, COUNT(*), SUM(amount)
        FROM transactions
        WHERE case_id = %s
        GROUP BY statement_id
    """, (case[0],))
    txns = cur.fetchall()
    print("Transactions per statement:")
    for t in txns:
        print(t)
        
    cur.execute("""
        SELECT statement_id, detector_name, score
        FROM detection_results
        WHERE case_id = %s
    """, (case[0],))
    results = cur.fetchall()
    print("Detection Results:")
    for r in results:
        print(r)

conn.close()
