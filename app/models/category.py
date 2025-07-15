from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String)  # Icon name or path
    color = Column(String)  # Hex color code
    is_active = Column(Boolean, default=True)
    
    # Relationships
    services = relationship("Service", back_populates="category") 