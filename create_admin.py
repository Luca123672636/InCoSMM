from app import app, db
from models import User
from werkzeug.security import generate_password_hash
from datetime import datetime

# Create an admin user with demo credentials
with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        # Create new admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('Admin123!'),
            first_name='Admin',
            last_name='User',
            role='admin',
            date_registered=datetime.now(),
            phone_number='+998123456789',
            is_active=True
        )
        
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: Admin123!")
    else:
        # Update existing admin password
        admin.password_hash = generate_password_hash('Admin123!')
        db.session.commit()
        print("Admin password reset to: Admin123!")