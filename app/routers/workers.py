from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.worker import Worker
from app.models.order import Review
from app.schemas.worker import (
    WorkerUpdate, WorkerResponse
)
from app.schemas.order import ReviewResponse
from app.routers.auth import get_current_user
from app.services.worker_service import WorkerService
from sqlalchemy.orm import joinedload
import os

router = APIRouter(prefix="/workers", tags=["workers"])


def get_public_image_url(image_path: str, request: Request) -> str:
    if not image_path:
        return None
    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path
    if image_path.startswith("/static/"):
        return f"{request.url.scheme}://{request.url.netloc}{image_path}"
    filename = os.path.basename(image_path)
    return f"{request.url.scheme}://{request.url.netloc}/static/{filename}"


@router.get("/profile", response_model=WorkerResponse)
async def get_worker_profile(request: Request, current_worker: Worker = Depends(get_current_user)):
    """Get current worker's profile"""
    worker_dict = current_worker.__dict__.copy()
    worker_dict["image"] = get_public_image_url(current_worker.image, request) if current_worker.image else None
    return worker_dict


@router.put("/profile", response_model=WorkerResponse)
async def update_worker_profile(
    worker_update: WorkerUpdate,
    request: Request,
    current_worker: Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update worker's basic profile"""
    for field, value in worker_update.dict(exclude_unset=True).items():
        setattr(current_worker, field, value)
    
    db.commit()
    db.refresh(current_worker)
    worker_dict = current_worker.__dict__.copy()
    worker_dict["image"] = get_public_image_url(current_worker.image, request) if current_worker.image else None
    return worker_dict

@router.post("/upload-profile-image")
async def upload_worker_profile_image(request: Request, file: UploadFile = File(...)):
    """Upload a profile image for the worker. Returns the public URL."""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'static')
    os.makedirs(static_dir, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"worker_{os.urandom(8).hex()}{file_ext}"
    file_path = os.path.join(static_dir, filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    public_url = f"{request.url.scheme}://{request.url.netloc}/static/{filename}"
    return {"url": public_url}

@router.get("/", response_model=List[WorkerResponse])
def get_workers(
    category_id: int = None,
    available_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all workers with optional filtering"""
    query = db.query(Worker).filter(Worker.is_active == True)
    
    if available_only:
        query = query.filter(Worker.is_available == True)
    
    if category_id:
        # Filter by category through services
        from app.models.service import Service
        query = query.join(Service, Worker.id == Service.worker_id).filter(Service.category_id == category_id)
    
    workers = query.all()
    return workers

@router.get("/{worker_id}", response_model=WorkerResponse)
def get_worker(worker_id: int, db: Session = Depends(get_db)):
    """Get a specific worker by ID"""
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    return worker

@router.get("/{worker_id}/reviews", response_model=List[ReviewResponse])
def get_worker_reviews(worker_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a specific worker"""
    # Check if worker exists
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    reviews = db.query(Review).options(
        joinedload(Review.user)
    ).filter(Review.worker_id == worker_id).all()
    return reviews 