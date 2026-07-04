import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("""
    SELECT c.title, s.filename, s.suspicion_score
    FROM statements s
    JOIN cases c ON c.id = s.case_id
    ORDER BY c.created_at DESC, s.created_at ASC
    LIMIT 15
""")
stmts = cur.fetchall()

for s in stmts:
    print(s)

conn.close()
