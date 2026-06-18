import os
import sys

# Add project root to sys.path so 'app' module can be discovered
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.config import config
from app.models.user import User


def create_admin_if_missing():
    # Use default config name; app factory isn't used because we want a minimal seed.
    config_name = os.environ.get('FLASK_CONFIG', 'default')

    # Expect DATABASE_URL etc. in .env for app/config.py
    # Create a temporary Flask app context from config object.
    from flask import Flask

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)

    with app.app_context():
        email = 'admin@fintelligence.io'
        admin = User.query.filter_by(email=email).first()
        if admin:
            print(f"Admin already exists: {email} ({admin.id})")
            return

        password = 'Admin@2026'
        hashed = generate_password_hash(password)

        admin = User(
            name='Admin',
            email=email,
            password_hash=hashed,
            role='admin',
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Seeded admin: {email} ({admin.id})")


if __name__ == '__main__':
    create_admin_if_missing()
