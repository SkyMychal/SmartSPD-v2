"""
TPA (Third Party Administrator) model
"""
from sqlalchemy import Column, String, Text, Boolean, JSON, Integer
from sqlalchemy.orm import relationship
from .base import BaseModel

class TPA(BaseModel):
    """Third Party Administrator model"""
    __tablename__ = "tpas"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    
    # Address information
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    country = Column(String(100), default="United States")
    
    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, default=dict)  # Custom TPA settings
    branding = Column(JSON, default=dict)  # Logo, colors, etc.
    
    # Subscription info
    subscription_tier = Column(String(50), default="basic")
    max_users = Column(Integer, default=10)
    max_health_plans = Column(Integer, default=5)
    max_documents = Column(Integer, default=100)
    
    # Relationships
    users = relationship("User", back_populates="tpa", cascade="all, delete-orphan")
    health_plans = relationship("HealthPlan", back_populates="tpa", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tpa", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TPA(name='{self.name}', slug='{self.slug}')>"