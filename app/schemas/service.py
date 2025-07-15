from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .category import CategoryResponse
from .worker import WorkerResponse


class ServiceBase(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: int
    hourly_rate: float
    minimum_hours: Optional[int] = 1


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    hourly_rate: Optional[float] = None
    minimum_hours: Optional[int] = None
    is_available: Optional[bool] = None


class ServiceResponse(ServiceBase):
    id: int
    worker_id: int
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    category: CategoryResponse
    worker: WorkerResponse
    
    class Config:
        from_attributes = True 