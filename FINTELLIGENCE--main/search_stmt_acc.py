import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("""
    SELECT id, case_id, account_number, filename
    FROM statements
    WHERE account_number ILIKE '%ACC%'
""")
stmts = cur.fetchall()

print("Statements with ACC in account_number:")
for s in stmts:
    print(s)

conn.close()
