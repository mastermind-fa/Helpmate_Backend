from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_admin():
    db = SessionLocal()
    email = "admin@gmail.com"
    password = "admin123"
    hashed_password = get_password_hash(password)

    # Check if admin already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        # Update values using SQLAlchemy ORM setattr
        setattr(existing, "hashed_password", hashed_password)
        setattr(existing, "is_admin", True)
        db.commit()
        print("Admin user already exists. Password updated to 'admin123'.")
        return

    admin_user = User(
        email=email,
        full_name="Admin User",
        hashed_password=hashed_password,
        is_active=True,
        is_verified=True,
        is_admin=True,
    )
    db.add(admin_user)
    db.commit()
    print("Admin user created!")

if __name__ == "__main__":
    create_admin() 