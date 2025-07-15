from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, UserFavorite
from app.models.worker import Worker
from app.routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/favorites", tags=["favorites"])

class FavoriteRequest(BaseModel):
    worker_id: int

@router.post("/", status_code=200)
def add_favorite(data: FavoriteRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not isinstance(current_user, User):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only users can add favorites")
    worker = db.query(Worker).filter(Worker.id == data.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    existing = db.query(UserFavorite).filter_by(user_id=current_user.id, worker_id=data.worker_id).first()
    if existing:
        return {"message": "Already in favorites"}
    fav = UserFavorite(user_id=current_user.id, worker_id=data.worker_id)
    db.add(fav)
    db.commit()
    return {"message": "Added to favorites"}

@router.delete("/{worker_id}", status_code=200)
def remove_favorite(worker_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not isinstance(current_user, User):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only users can remove favorites")
    fav = db.query(UserFavorite).filter_by(user_id=current_user.id, worker_id=worker_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()
    return {"message": "Removed from favorites"}

@router.get("/", status_code=200)
def list_favorites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not isinstance(current_user, User):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only users can view favorites")
    favs = db.query(UserFavorite).filter_by(user_id=current_user.id).all()
    result = []
    for fav in favs:
        worker = db.query(Worker).filter(Worker.id == fav.worker_id).first()
        result.append({
            "id": fav.id,
            "worker_id": fav.worker_id,
            "created_at": fav.created_at,
            "worker": worker.__dict__ if worker else None
        })
    return result

@router.get("/check/{worker_id}", status_code=200)
def check_favorite(worker_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not isinstance(current_user, User):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only users can check favorites")
    fav = db.query(UserFavorite).filter_by(user_id=current_user.id, worker_id=worker_id).first()
    return {"is_favorite": fav is not None} 