from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .user import UserResponse
from .worker import WorkerResponse
from .service import ServiceResponse


class OrderBase(BaseModel):
    service_id: int
    description: Optional[str] = None
    hours: Optional[int] = 1
    scheduled_date: Optional[datetime] = None
    payment_method: Optional[str] = "pay_in_person"  # pay_in_advance, pay_in_person


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    description: Optional[str] = None
    hours: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    status: Optional[str] = None


class OrderResponse(OrderBase):
    id: int
    user_id: int
    worker_id: int
    total_amount: float
    status: str
    payment_method: str
    completed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: UserResponse
    worker: WorkerResponse
    service: ServiceResponse
    
    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    rating: int  # 1-5
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    worker_id: int
    order_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    user: UserResponse
    worker: WorkerResponse
    
    class Config:
        from_attributes = True 