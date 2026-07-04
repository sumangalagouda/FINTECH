import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("""
    SELECT s.id, t.date, t.type, t.amount, t.sender_account, t.receiver_account
    FROM statements s
    JOIN transactions t ON s.id = t.statement_id
    WHERE s.case_id = 'c9408e25-19b9-4ef5-b750-7678c63f981d'
    ORDER BY s.id, t.date, t.amount
""")
txns = cur.fetchall()

print("Transactions by Statement:")
for t in txns:
    print(t)

conn.close()
