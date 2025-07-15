from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class WorkerCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = []
    hourly_rate: float
    experience_years: Optional[int] = None
    category_id: int  # For automatic service creation


class WorkerLogin(BaseModel):
    email: EmailStr
    password: str


class WorkerResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone_number: Optional[str] = None
    address: Optional[str] = None
    image: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = []
    hourly_rate: float
    experience_years: Optional[int] = None
    is_available: bool
    rating: float
    total_reviews: int
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = None
    hourly_rate: Optional[float] = None
    experience_years: Optional[int] = None
    is_available: Optional[bool] = None
    image: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str 