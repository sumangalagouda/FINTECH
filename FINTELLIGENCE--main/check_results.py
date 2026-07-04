import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("""
    SELECT statement_id, detector_name, score, triggered
    FROM detection_results
    WHERE case_id = 'c9408e25-19b9-4ef5-b750-7678c63f981d'
""")
results = cur.fetchall()

for r in results:
    print(r)

conn.close()
