from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.core.database import get_db
from app.models.order import Order, Review
from app.models.user import User
from app.models.service import Service
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, ReviewCreate, ReviewResponse
from app.routers.auth import get_current_user
from app.models.worker import Worker
import asyncio
from app.models.notification import Notification

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Create a new order (only users can create orders)"""
    # Verify the user is creating the order
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can create orders"
        )
    
    # Check if the service exists and is available
    from app.models.service import Service
    from app.models.worker import Worker
    
    service = db.query(Service).filter(Service.id == order.service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    if not service.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service is not available"
        )
    
    # Check if worker exists and is available
    worker = db.query(Worker).filter(Worker.id == service.worker_id).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    if not worker.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Worker is currently not available for booking"
        )
    
    # Check for time conflicts if scheduled_date is provided
    if order.scheduled_date:
        # Check if worker has any overlapping orders at the same time
        from datetime import timedelta
        
        # Calculate the end time of the requested booking
        end_time = order.scheduled_date + timedelta(hours=order.hours)
        
        # Check for overlapping orders using a subquery approach
        from sqlalchemy import text
        
        # Use raw SQL for the complex time overlap check
        overlap_query = text("""
            SELECT * FROM orders 
            WHERE worker_id = :worker_id 
            AND status IN ('pending', 'accepted', 'in_progress')
            AND scheduled_date IS NOT NULL
            AND (
                (scheduled_date <= :new_start AND datetime(scheduled_date, '+' || hours || ' hours') > :new_start)
                OR (scheduled_date < :new_end AND datetime(scheduled_date, '+' || hours || ' hours') >= :new_end)
                OR (scheduled_date >= :new_start AND datetime(scheduled_date, '+' || hours || ' hours') <= :new_end)
            )
        """)
        
        conflicting_orders = db.execute(
            overlap_query,
            {
                'worker_id': worker.id,
                'new_start': order.scheduled_date,
                'new_end': end_time
            }
        ).first()
        
        if conflicting_orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sorry, the worker is already booked at this time. Please choose another date and time."
            )
    
    # Calculate total amount
    total_amount = service.hourly_rate * order.hours
    
    # Create order
    db_order = Order(
        user_id=current_user.id,
        worker_id=service.worker_id,
        service_id=order.service_id,
        description=order.description,
        hours=order.hours,
        total_amount=total_amount,
        payment_method=order.payment_method,
        scheduled_date=order.scheduled_date
    )
    db.add(db_order)
    
    db.commit()
    db.refresh(db_order)
    # Create notifications for user and worker
    notif_title = "Order Booked"
    notif_msg = f"Your order (ID: {db_order.id}) has been booked. Description: {db_order.description}"
    user_notif = Notification(
        user_id=current_user.id,
        type="order_booked",
        title=notif_title,
        message=notif_msg
    )
    worker_notif = Notification(
        worker_id=worker.id,
        type="order_booked",
        title=notif_title,
        message=notif_msg
    )
    db.add(user_notif)
    db.add(worker_notif)
    db.commit()
    # Send notification emails to user and worker
    if background_tasks is not None:
        from app.services.email_service import email_service
        background_tasks.add_task(
            lambda: asyncio.run(email_service.send_order_booked_email(current_user, worker, db_order))
        )
    return db_order


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all orders for the current user"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can access this endpoint"
        )
    
    orders = db.query(Order).options(
        joinedload(Order.service).joinedload(Service.category),
        joinedload(Order.worker),
        joinedload(Order.user)
    ).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific order by ID"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can access this endpoint"
        )
    
    order = db.query(Order).options(
        joinedload(Order.service).joinedload(Service.category),
        joinedload(Order.worker),
        joinedload(Order.user)
    ).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Update an order (only the order owner can update)"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can update orders"
        )
    
    db_order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or you don't have permission to update it"
        )
    
    # Track if status is being set to completed
    status_was_completed = db_order.status == "completed"
    # Update order fields
    for field, value in order_update.dict(exclude_unset=True).items():
        setattr(db_order, field, value)
    db.commit()
    db.refresh(db_order)
    # If status changed to completed, send notification and create notification records
    if not status_was_completed and db_order.status == "completed":
        from app.models.user import User
        from app.models.worker import Worker
        user = db.query(User).filter(User.id == db_order.user_id).first()
        worker = db.query(Worker).filter(Worker.id == db_order.worker_id).first()
        notif_title = "Order Completed"
        notif_msg = f"Your order (ID: {db_order.id}) has been marked as completed. Description: {db_order.description}"
        user_notif = Notification(
            user_id=user.id,
            type="order_completed",
            title=notif_title,
            message=notif_msg
        )
        worker_notif = Notification(
            worker_id=worker.id,
            type="order_completed",
            title=notif_title,
            message=notif_msg
        )
        db.add(user_notif)
        db.add(worker_notif)
        db.commit()
        if background_tasks is not None:
            from app.services.email_service import email_service
            background_tasks.add_task(
                lambda: asyncio.run(email_service.send_order_completed_email(user, worker, db_order))
            )
    return db_order


@router.delete("/{order_id}")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel an order (only the order owner can cancel)"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can cancel orders"
        )
    
    db_order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or you don't have permission to cancel it"
        )
    
    if db_order.status in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed or already cancelled order"
        )
    
    db_order.status = "cancelled"
    
    db.commit()
    return {"message": "Order cancelled successfully"}


# Reviews
@router.post("/{order_id}/review", response_model=ReviewResponse)
async def create_review(
    order_id: int,
    review: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a review for an order (only users can create reviews)"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can create reviews"
        )
    
    # Check if order exists and belongs to the user
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only review completed orders"
        )
    
    # Check if review already exists
    existing_review = db.query(Review).filter(Review.order_id == order_id).first()
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already exists for this order"
        )
    
    # Validate rating
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    # Create review
    db_review = Review(
        user_id=current_user.id,
        worker_id=order.worker_id,
        order_id=order_id,
        rating=review.rating,
        comment=review.comment
    )
    db.add(db_review)
    
    # Update worker's rating
    from app.models.worker import Worker
    worker = db.query(Worker).filter(Worker.id == order.worker_id).first()
    if worker:
        # Calculate new average rating
        total_reviews = worker.total_reviews + 1
        new_rating = ((worker.rating * worker.total_reviews) + review.rating) / total_reviews
        worker.rating = new_rating
        worker.total_reviews = total_reviews
    
    db.commit()
    db.refresh(db_review)
    return db_review


@router.get("/{order_id}/review", response_model=ReviewResponse)
async def get_review(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get review for a specific order"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can access this endpoint"
        )
    
    # Check if order exists and belongs to the user
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    review = db.query(Review).filter(Review.order_id == order_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return review 

@router.get("/worker/pending", response_model=List[OrderResponse])
async def get_pending_orders_for_worker(
    current_worker: Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending orders assigned to the current worker"""
    if not isinstance(current_worker, Worker):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only workers can access this endpoint")
    orders = db.query(Order).options(
        joinedload(Order.service).joinedload(Service.category),
        joinedload(Order.user)
    ).filter(
        Order.worker_id == current_worker.id,
        Order.status == "pending"
    ).order_by(Order.created_at.desc()).all()
    return orders

@router.get("/worker/completed", response_model=List[OrderResponse])
async def get_completed_orders_for_worker(
    current_worker: Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all completed orders assigned to the current worker"""
    if not isinstance(current_worker, Worker):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only workers can access this endpoint")
    orders = db.query(Order).options(
        joinedload(Order.service).joinedload(Service.category),
        joinedload(Order.user)
    ).filter(
        Order.worker_id == current_worker.id,
        Order.status == "completed"
    ).order_by(Order.created_at.desc()).all()
    return orders 