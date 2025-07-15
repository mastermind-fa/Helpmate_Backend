from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    
    # Order details
    description = Column(Text)
    hours = Column(Integer, default=1)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, accepted, in_progress, completed, cancelled
    payment_method = Column(String, default="pay_in_person")  # pay_in_advance, pay_in_person
    
    # Scheduling
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="orders")
    worker = relationship("Worker", back_populates="orders_received")
    service = relationship("Service", back_populates="orders")
    review = relationship("Review", back_populates="order", uselist=False)


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Review details
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    worker = relationship("Worker", back_populates="reviews_received")
    order = relationship("Order", back_populates="review") 