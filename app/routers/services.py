from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.service import Service
from app.models.worker import Worker
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.routers.auth import get_current_user

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/", response_model=List[ServiceResponse])
def get_services(
    category_id: int = None,
    worker_id: int = None,
    available_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all services with optional filtering"""
    query = db.query(Service)
    
    if available_only:
        query = query.filter(Service.is_available == True)
    
    if category_id:
        query = query.filter(Service.category_id == category_id)
    
    if worker_id:
        query = query.filter(Service.worker_id == worker_id)
    
    services = query.all()
    return services


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: int, db: Session = Depends(get_db)):
    """Get a specific service by ID"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    return service


@router.post("/", response_model=ServiceResponse)
async def create_service(
    service: ServiceCreate,
    current_worker: Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new service (only workers can create services)"""
    # Verify the worker is creating the service
    if not isinstance(current_worker, Worker):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can create services"
        )
    
    # Check if category exists
    from app.models.category import Category
    category = db.query(Category).filter(Category.id == service.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Create service
    db_service = Service(
        **service.dict(),
        worker_id=current_worker.id
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    service_update: ServiceUpdate,
    current_worker: Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a service (only the service owner can update)"""
    # Verify the worker is updating their own service
    if not isinstance(current_worker, Worker):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can update services"
        )
    
    db_service = db.query(Service).filter(
        Service.id == service_id,
        Service.worker_id == current_worker.id
    ).first()
    
    if not db_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or you don't have permission to update it"
        )
    
    # Update service fields
    for field, value in service_update.dict(exclude_unset=True).items():
        setattr(db_service, field, value)
    
    db.commit()
    db.refresh(db_service)
    return db_service


@router.delete("/{service_id}")
async def delete_service(
    service_id: int,
    current_worker: Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a service (only the service owner can delete)"""
    # Verify the worker is deleting their own service
    if not isinstance(current_worker, Worker):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can delete services"
        )
    
    db_service = db.query(Service).filter(
        Service.id == service_id,
        Service.worker_id == current_worker.id
    ).first()
    
    if not db_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or you don't have permission to delete it"
        )
    
    # Soft delete by setting is_available to False
    db_service.is_available = False
    db.commit()
    return {"message": "Service deleted successfully"}


@router.get("/worker/my-services", response_model=List[ServiceResponse])
async def get_my_services(
    current_worker: Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all services created by the current worker"""
    if not isinstance(current_worker, Worker):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can access this endpoint"
        )
    
    services = db.query(Service).filter(Service.worker_id == current_worker.id).all()
    return services 