import psycopg2
import json

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("""
    SELECT raw_text
    FROM transactions
    WHERE case_id = 'c9408e25-19b9-4ef5-b750-7678c63f981d'
    AND description ILIKE 'IMPS TO X2%'
""")
txns = cur.fetchall()

for t in txns:
    print(t[0])

conn.close()
