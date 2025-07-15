from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import Worker, Service, Category

def fix_worker_services():
    db = SessionLocal()
    
    try:
        # Get all categories
        categories = {cat.name.lower(): cat.id for cat in db.query(Category).all()}
        print("Available categories:", list(categories.keys()))
        
        # Fix existing services with missing or wrong category_id
        all_services = db.query(Service).all()
        for service in all_services:
            if not service.category_id or service.category_id not in categories.values():
                # Try to map by title
                title_lower = service.title.lower()
                mapped_category = None
                for cat_name in categories.keys():
                    if cat_name in title_lower:
                        mapped_category = categories[cat_name]
                        break
                if mapped_category:
                    print(f"Fixing service '{service.title}' (ID: {service.id}) to category '{cat_name}' (ID: {mapped_category})")
                    service.category_id = mapped_category
                else:
                    print(f"Could not map service '{service.title}' (ID: {service.id}) to any category!")
        db.commit()
        
        # Get workers without services
        workers_without_services = db.query(Worker).filter(
            ~Worker.id.in_(
                db.query(Service.worker_id).distinct()
            )
        ).all()
        
        print(f"\nFound {len(workers_without_services)} workers without services:")
        
        for worker in workers_without_services:
            print(f"\nWorker: {worker.full_name} (ID: {worker.id})")
            print(f"Skills: {worker.skills}")
            
            if not worker.skills:
                print("  No skills found, skipping...")
                continue
            
            # Map skills to categories
            services_to_create = []
            
            for skill in worker.skills:
                skill_lower = skill.lower()
                category_id = None
                service_title = None
                
                # Map skills to categories
                if any(keyword in skill_lower for keyword in ['plumb', 'pipe', 'water']):
                    category_id = categories.get('plumber')
                    service_title = f"Professional {skill}"
                elif any(keyword in skill_lower for keyword in ['clean', 'cleaning', 'house']):
                    category_id = categories.get('cleaner')
                    service_title = f"Professional {skill}"
                elif any(keyword in skill_lower for keyword in ['electrical', 'electric', 'wiring']):
                    category_id = categories.get('electrician')
                    service_title = f"Professional {skill}"
                elif any(keyword in skill_lower for keyword in ['child', 'babysit', 'care']):
                    category_id = categories.get('babysitting')
                    service_title = f"Professional {skill}"
                elif any(keyword in skill_lower for keyword in ['ac', 'air', 'cooling']):
                    category_id = categories.get('ac repair')
                    service_title = f"Professional {skill}"
                elif any(keyword in skill_lower for keyword in ['tutor', 'math', 'science', 'english', 'homework']):
                    category_id = categories.get('tutoring')
                    service_title = f"Professional {skill}"
                elif any(keyword in skill_lower for keyword in ['medical', 'physician', 'doctor']):
                    category_id = categories.get('physician')
                    service_title = f"Professional {skill}"
                elif any(keyword in skill_lower for keyword in ['carpent', 'wood', 'handyman']):
                    category_id = categories.get('carpenter')
                    service_title = f"Professional {skill}"
                elif any(keyword in skill_lower for keyword in ['garden', 'landscape']):
                    category_id = categories.get('gardener')
                    service_title = f"Professional {skill}"
                elif any(keyword in skill_lower for keyword in ['cook', 'chef', 'food']):
                    category_id = categories.get('cook')
                    service_title = f"Professional {skill}"
                elif any(keyword in skill_lower for keyword in ['drive', 'transport']):
                    category_id = categories.get('driver')
                    service_title = f"Professional {skill}"
                elif any(keyword in skill_lower for keyword in ['security', 'guard']):
                    category_id = categories.get('security')
                    service_title = f"Professional {skill}"
                
                if category_id and service_title:
                    # Check if service already exists
                    existing_service = db.query(Service).filter(
                        Service.worker_id == worker.id,
                        Service.category_id == category_id
                    ).first()
                    
                    if not existing_service:
                        services_to_create.append({
                            'title': service_title,
                            'description': f"Professional {skill} service by {worker.full_name}",
                            'category_id': category_id,
                            'worker_id': worker.id,
                            'hourly_rate': worker.hourly_rate or 20.0,
                            'minimum_hours': 1,
                            'is_available': worker.is_available
                        })
                        print(f"  Will create service: {service_title} (Category: {list(categories.keys())[list(categories.values()).index(category_id)]})")
                    else:
                        print(f"  Service already exists: {existing_service.title}")
            
            # Create services
            for service_data in services_to_create:
                service = Service(**service_data)
                db.add(service)
                print(f"  Created service: {service_data['title']}")
        
        db.commit()
        print(f"\n✅ Successfully created/fixed services for workers!")
        
        # Show summary
        print("\n--- SUMMARY ---")
        all_workers = db.query(Worker).all()
        for worker in all_workers:
            services = db.query(Service).filter(Service.worker_id == worker.id).all()
            print(f"{worker.full_name}: {len(services)} services")
            for service in services:
                category = db.query(Category).filter(Category.id == service.category_id).first()
                print(f"  - {service.title} (Category: {category.name if category else 'None'})")
        
    except Exception as e:
        print(f"Error fixing worker services: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_worker_services() 