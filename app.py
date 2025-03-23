import os
import logging
from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Configure logging
logging.basicConfig(level=logging.DEBUG)


class Base(DeclarativeBase):
    pass


# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development_secret_key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///attendance.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)

# Configure login manager
login_manager.login_view = 'login'
login_manager.login_message = 'Iltimos, avval tizimga kiring.'
login_manager.login_message_category = 'warning'

# Initialize app context
with app.app_context():
    # Import models and routes after app is created to avoid circular imports
    from models import User
    import routes
    
    # Register user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create database tables
    db.create_all()
    
    # Add first admin if no users exist
    if not User.query.first():
        from werkzeug.security import generate_password_hash
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            first_name='Admin',
            last_name='User',
            role='admin',
            date_registered=datetime.now()
        )
        db.session.add(admin)
        db.session.commit()
        app.logger.info('Initial admin user created.')

# Add context processors for templates
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Register routes
from routes import *
