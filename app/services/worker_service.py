from sqlalchemy.orm import Session
from app.models import Worker, Service, Category
from app.schemas.worker import WorkerCreate
from typing import List, Dict

class WorkerService:
    
    @staticmethod
    def create_worker_with_services(db: Session, worker_data: dict) -> Worker:
        """Create a worker and automatically create services based on skills or selected category"""
        
        # Create the worker first
        worker = Worker(
            email=worker_data['email'],
            full_name=worker_data['full_name'],
            hashed_password=worker_data['hashed_password'],
            phone_number=worker_data.get('phone_number'),
            address=worker_data.get('address'),
            bio=worker_data.get('bio'),
            skills=worker_data.get('skills'),
            hourly_rate=worker_data.get('hourly_rate'),
            experience_years=worker_data.get('experience_years'),
            is_available=worker_data.get('is_available', True),
            is_verified=worker_data.get('is_verified', False),
            is_active=worker_data.get('is_active', False)
        )
        
        db.add(worker)
        db.flush()  # Get the worker ID without committing
        
        # If category_id is provided, create a service for that category
        if worker_data.get('category_id'):
            category_id = worker_data['category_id']
            from app.models.category import Category
            category = db.query(Category).filter(Category.id == category_id).first()
            if category:
                service = Service(
                    title=f"Professional {category.name}",
                    description=f"Professional {category.name} service by {worker.full_name}",
                    category_id=category_id,
                    worker_id=worker.id,
                    hourly_rate=worker.hourly_rate or 20.0,
                    minimum_hours=1,
                    is_available=worker.is_available
                )
                db.add(service)
                db.flush()
        # Otherwise, create services based on skills
        elif worker_data.get('skills'):
            WorkerService._create_services_from_skills(db, worker, worker_data['skills'])
        
        db.commit()
        db.refresh(worker)
        return worker
    
    @staticmethod
    def _create_services_from_skills(db: Session, worker: Worker, skills: List[str]) -> None:
        """Create services for a worker based on their skills"""
        
        # Get all categories
        categories = {cat.name.lower(): cat.id for cat in db.query(Category).all()}
        
        # Skill to category mapping
        skill_category_mapping = {
            'plumbing': 'plumber',
            'pipe': 'plumber',
            'water': 'plumber',
            'clean': 'cleaner',
            'cleaning': 'cleaner',
            'house': 'cleaner',
            'electrical': 'electrician',
            'electric': 'electrician',
            'wiring': 'electrician',
            'child': 'babysitting',
            'babysit': 'babysitting',
            'care': 'babysitting',
            'ac': 'ac repair',
            'air': 'ac repair',
            'cooling': 'ac repair',
            'tutor': 'tutoring',
            'math': 'tutoring',
            'science': 'tutoring',
            'english': 'tutoring',
            'homework': 'tutoring',
            'medical': 'physician',
            'physician': 'physician',
            'doctor': 'physician',
            'carpent': 'carpenter',
            'wood': 'carpenter',
            'handyman': 'carpenter',
            'garden': 'gardener',
            'landscape': 'gardener',
            'cook': 'cook',
            'chef': 'cook',
            'food': 'cook',
            'drive': 'driver',
            'transport': 'driver',
            'security': 'security',
            'guard': 'security'
        }
        
        created_services = []
        
        for skill in skills:
            skill_lower = skill.lower()
            category_name = None
            
            # Find matching category
            for keyword, category in skill_category_mapping.items():
                if keyword in skill_lower:
                    category_name = category
                    break
            
            if category_name and category_name in categories:
                category_id = categories[category_name]
                
                # Check if service already exists for this worker and category
                existing_service = db.query(Service).filter(
                    Service.worker_id == worker.id,
                    Service.category_id == category_id
                ).first()
                
                if not existing_service:
                    service = Service(
                        title=f"Professional {skill}",
                        description=f"Professional {skill} service by {worker.full_name}",
                        category_id=category_id,
                        worker_id=worker.id,
                        hourly_rate=worker.hourly_rate or 20.0,
                        minimum_hours=1,
                        is_available=worker.is_available
                    )
                    db.add(service)
                    created_services.append(service)
        
        if created_services:
            db.flush()  # Flush to get service IDs
    
    @staticmethod
    def update_worker_services(db: Session, worker_id: int, skills: List[str]) -> None:
        """Update worker's services based on new skills"""
        
        # Get the worker
        worker = db.query(Worker).filter(Worker.id == worker_id).first()
        if not worker:
            return
        
        # Remove existing services
        db.query(Service).filter(Service.worker_id == worker_id).delete()
        
        # Create new services based on skills
        WorkerService._create_services_from_skills(db, worker, skills)
        
        db.commit() 