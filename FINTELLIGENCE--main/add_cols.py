from app.extensions import db
from app import create_app
import sqlalchemy

app = create_app()

with app.app_context():
    try:
        db.session.execute(sqlalchemy.text('ALTER TABLE statements ADD COLUMN suspicion_score FLOAT DEFAULT 0.0'))
        print("Added suspicion_score")
    except Exception as e:
        print(e)
    try:
        db.session.execute(sqlalchemy.text('ALTER TABLE statements ADD COLUMN risk_level VARCHAR(50) DEFAULT \'low\''))
        print("Added risk_level")
    except Exception as e:
        print(e)
    try:
        db.session.execute(sqlalchemy.text('ALTER TABLE statements ADD COLUMN severity VARCHAR(50) DEFAULT \'low\''))
        print("Added severity")
    except Exception as e:
        print(e)
    try:
        db.session.execute(sqlalchemy.text('ALTER TABLE statements ADD COLUMN ai_summary TEXT'))
        print("Added ai_summary")
    except Exception as e:
        print(e)
        
    db.session.commit()
    print("Done")
