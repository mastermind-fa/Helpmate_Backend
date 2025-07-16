from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_admin():
    db = SessionLocal()
    try:
        admin_email = "admin@gmail.com"
        admin_password = "admin123"
        admin = db.query(User).filter(User.email == admin_email).first()
        if admin:
            print("Admin user already exists.")
            return
        hashed_password = get_password_hash(admin_password)
        admin = User(
            email=admin_email,
            full_name="Admin",
            hashed_password=hashed_password,
            phone_number="",
            address="",
            is_active=True,
            is_verified=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        print("Admin user created successfully.")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin() 