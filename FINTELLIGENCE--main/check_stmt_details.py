import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("""
    SELECT s.id, s.filename, s.account_number, s.account_holder, s.suspicion_score
    FROM statements s
    JOIN cases c ON c.id = s.case_id
    WHERE c.title = 'Investigation: 61577175569879.pdf'
    ORDER BY s.created_at
""")
stmts = cur.fetchall()

for s in stmts:
    print(s)

conn.close()
