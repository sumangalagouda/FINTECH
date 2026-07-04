import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("""
    SELECT t.id, t.description, t.raw_text, t.sender_account, t.receiver_account
    FROM transactions t
    WHERE t.description ILIKE '%ACC1001%' OR t.raw_text ILIKE '%ACC1001%'
    LIMIT 5
""")
txns = cur.fetchall()

for t in txns:
    print(t)

conn.close()
