from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import Category, User, Worker
from app.core.security import get_password_hash

def init_db():
    db = SessionLocal()
    
    try:
        # Create sample categories
        categories_data = [
            {
                "name": "Babysitting",
                "description": "Professional childcare services",
                "icon": "child_care",
                "color": "#E91E63"
            },
            {
                "name": "AC Repair",
                "description": "Air conditioning repair and maintenance",
                "icon": "ac_unit",
                "color": "#2196F3"
            },
            {
                "name": "Tutoring",
                "description": "Educational tutoring services",
                "icon": "school",
                "color": "#FF9800"
            },
            {
                "name": "Physician",
                "description": "Medical consultation and care",
                "icon": "medical_services",
                "color": "#F44336"
            },
            {
                "name": "Cleaner",
                "description": "House cleaning and maintenance",
                "icon": "cleaning_services",
                "color": "#4CAF50"
            },
            {
                "name": "Plumber",
                "description": "Plumbing repair and installation",
                "icon": "plumbing",
                "color": "#3F51B5"
            },
            {
                "name": "Electrician",
                "description": "Electrical repair and installation",
                "icon": "electrical_services",
                "color": "#FFC107"
            },
            {
                "name": "Carpenter",
                "description": "Carpentry and woodwork services",
                "icon": "handyman",
                "color": "#795548"
            },
            {
                "name": "Gardener",
                "description": "Garden maintenance and landscaping",
                "icon": "eco",
                "color": "#8BC34A"
            },
            {
                "name": "Cook",
                "description": "Professional cooking and catering",
                "icon": "restaurant",
                "color": "#FF5722"
            },
            {
                "name": "Driver",
                "description": "Transportation and driving services",
                "icon": "drive_eta",
                "color": "#009688"
            },
            {
                "name": "Security",
                "description": "Security and protection services",
                "icon": "security",
                "color": "#607D8B"
            }
        ]
        
        # Check if categories already exist
        existing_categories = db.query(Category).count()
        if existing_categories == 0:
            for category_data in categories_data:
                category = Category(**category_data)
                db.add(category)
            print("Categories created successfully!")
        else:
            print("Categories already exist, skipping...")
        
        # Create sample users
        users_data = [
            {
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "password": "password123",
                "phone_number": "+1234567890",
                "address": "123 Main St, City, State"
            },
            {
                "email": "jane.smith@example.com",
                "full_name": "Jane Smith",
                "password": "password123",
                "phone_number": "+1234567891",
                "address": "456 Oak Ave, City, State"
            }
        ]
        
        for user_data in users_data:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing_user:
                hashed_password = get_password_hash(user_data["password"])
                user = User(
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    hashed_password=hashed_password,
                    phone_number=user_data["phone_number"],
                    address=user_data["address"]
                )
                db.add(user)
        
        # Create sample workers
        workers_data = [
            {
                "email": "mike.plumber@example.com",
                "full_name": "Mike Johnson",
                "password": "password123",
                "phone_number": "+1234567892",
                "address": "789 Pine St, City, State",
                "bio": "Experienced plumber with 10+ years of experience",
                "skills": ["Plumbing", "Pipe Repair", "Installation"],
                "hourly_rate": 45.0,
                "experience_years": 10
            },
            {
                "email": "sarah.cleaner@example.com",
                "full_name": "Sarah Wilson",
                "password": "password123",
                "phone_number": "+1234567893",
                "address": "321 Elm St, City, State",
                "bio": "Professional cleaner specializing in residential cleaning",
                "skills": ["House Cleaning", "Deep Cleaning", "Organization"],
                "hourly_rate": 25.0,
                "experience_years": 5
            },
            {
                "email": "david.electrician@example.com",
                "full_name": "David Brown",
                "password": "password123",
                "phone_number": "+1234567894",
                "address": "654 Maple Dr, City, State",
                "bio": "Licensed electrician with expertise in residential and commercial work",
                "skills": ["Electrical Repair", "Installation", "Wiring"],
                "hourly_rate": 50.0,
                "experience_years": 8
            }
        ]
        
        for worker_data in workers_data:
            existing_worker = db.query(Worker).filter(Worker.email == worker_data["email"]).first()
            if not existing_worker:
                hashed_password = get_password_hash(worker_data["password"])
                worker = Worker(
                    email=worker_data["email"],
                    full_name=worker_data["full_name"],
                    hashed_password=hashed_password,
                    phone_number=worker_data["phone_number"],
                    address=worker_data["address"],
                    bio=worker_data["bio"],
                    skills=worker_data["skills"],
                    hourly_rate=worker_data["hourly_rate"],
                    experience_years=worker_data["experience_years"]
                )
                db.add(worker)
        
        db.commit()
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 