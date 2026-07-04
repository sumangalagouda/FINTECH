import psycopg2
import json

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("""
    SELECT *
    FROM transactions 
    WHERE case_id = 'c9408e25-19b9-4ef5-b750-7678c63f981d'
    LIMIT 2
""")
txns = cur.fetchall()

# Get column names
col_names = [desc[0] for desc in cur.description]

print(f"\nTRANSACTIONS SCHEMA:")
for i, t in enumerate(txns):
    print(f"\n--- Txn {i+1} ---")
    for j, col in enumerate(col_names):
        print(f"{col}: {t[j]}")

conn.close()
