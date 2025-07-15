from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.models.worker import Worker
from app.routers.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/user", response_model=List[dict])
def get_user_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not isinstance(current_user, User):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only users can access this endpoint")
    notifs = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).all()
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at
        } for n in notifs
    ]

@router.get("/worker", response_model=List[dict])
def get_worker_notifications(current_user: Worker = Depends(get_current_user), db: Session = Depends(get_db)):
    if not isinstance(current_user, Worker):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only workers can access this endpoint")
    notifs = db.query(Notification).filter(Notification.worker_id == current_user.id).order_by(Notification.created_at.desc()).all()
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at
        } for n in notifs
    ]

@router.put("/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    # Only allow owner to mark as read
    if (notif.user_id and hasattr(current_user, 'id') and notif.user_id != current_user.id) or (notif.worker_id and hasattr(current_user, 'id') and notif.worker_id != getattr(current_user, 'id', None)):
        raise HTTPException(status_code=403, detail="Not allowed")
    notif.is_read = True
    db.commit()
    return {"success": True, "notification_id": notification_id} 