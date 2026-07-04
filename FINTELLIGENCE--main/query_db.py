import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("SELECT id, case_id, filename, account_number FROM statements;")
statements = cur.fetchall()
print("Statements:")
for s in statements:
    print(s)

cur.execute("SELECT id, type, sender_account, receiver_account, statement_id FROM transactions LIMIT 10;")
txns = cur.fetchall()
print("\nTransactions:")
for t in txns:
    print(t)

conn.close()
