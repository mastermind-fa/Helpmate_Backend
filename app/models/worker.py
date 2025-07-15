from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Worker(Base):
    __tablename__ = "workers"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone_number = Column(String)
    address = Column(Text)
    image = Column(String, nullable=True)  # Optional profile image URL or path
    
    # Work Profile
    bio = Column(Text)
    skills = Column(JSON)  # List of skills
    hourly_rate = Column(Float)
    experience_years = Column(Integer)
    is_available = Column(Boolean, default=True)
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    # Verification
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    orders_received = relationship("Order", back_populates="worker")
    orders_placed = relationship("WorkerOrder", back_populates="worker")
    reviews_received = relationship("Review", back_populates="worker")
    chats = relationship("Chat", back_populates="worker")


class WorkerOrder(Base):
    __tablename__ = "worker_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)  # Worker placing the order
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)  # Service being ordered
    status = Column(String, default="pending")  # pending, accepted, completed, cancelled
    description = Column(Text)
    scheduled_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    worker = relationship("Worker", back_populates="orders_placed") 