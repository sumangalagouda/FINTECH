import sqlalchemy
import sys

db_url = 'postgresql://neondb_owner:npg_YakjfGdS80sM@ep-plain-snow-aobqr0pz-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

engine = sqlalchemy.create_engine(db_url)
try:
    with engine.connect() as conn:
        try:
            conn.execute(sqlalchemy.text('ALTER TABLE statements ADD COLUMN suspicion_score FLOAT DEFAULT 0.0'))
            print("Added suspicion_score")
        except Exception as e:
            print("score error:", e)
        
        try:
            conn.execute(sqlalchemy.text("ALTER TABLE statements ADD COLUMN risk_level VARCHAR(50) DEFAULT 'low'"))
            print("Added risk_level")
        except Exception as e:
            print("risk error:", e)
            
        try:
            conn.execute(sqlalchemy.text("ALTER TABLE statements ADD COLUMN severity VARCHAR(50) DEFAULT 'low'"))
            print("Added severity")
        except Exception as e:
            print("severity error:", e)
            
        try:
            conn.execute(sqlalchemy.text('ALTER TABLE statements ADD COLUMN ai_summary TEXT'))
            print("Added ai_summary")
        except Exception as e:
            print("summary error:", e)
            
        conn.commit()
except Exception as e:
    print("connection error:", e)
    sys.exit(1)
print("Done")
