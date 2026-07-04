import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("""
    SELECT id, filename, account_number, account_holder
    FROM statements
    WHERE case_id = 'c9408e25-19b9-4ef5-b750-7678c63f981d'
""")
stmts = cur.fetchall()

print("Statements:")
for s in stmts:
    print(s)

conn.close()
