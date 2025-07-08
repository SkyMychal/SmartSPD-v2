"""
Health Plan model for managing different insurance plans
"""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, Integer, DateTime, Numeric
from sqlalchemy.orm import relationship
from .base import TenantModel

class HealthPlan(TenantModel):
    """Health Plan model"""
    __tablename__ = "health_plans"
    
    # Basic info
    name = Column(String(255), nullable=False)
    plan_number = Column(String(100), nullable=False)
    group_id = Column(String(100), nullable=False)  # Required Group ID for TPA identification
    plan_year = Column(Integer, nullable=False)
    effective_date = Column(DateTime, nullable=False)
    termination_date = Column(DateTime)
    
    # Plan details
    plan_type = Column(String(50))  # PPO, HMO, HDHP, etc.
    description = Column(Text)
    
    # Coverage details from BPS
    deductible_individual = Column(Numeric(10, 2))
    deductible_family = Column(Numeric(10, 2))
    out_of_pocket_max_individual = Column(Numeric(10, 2))
    out_of_pocket_max_family = Column(Numeric(10, 2))
    
    # Copay information
    primary_care_copay = Column(Numeric(10, 2))
    specialist_copay = Column(Numeric(10, 2))
    urgent_care_copay = Column(Numeric(10, 2))
    emergency_room_copay = Column(Numeric(10, 2))
    
    # Coinsurance
    in_network_coinsurance = Column(Numeric(5, 2))  # e.g., 20.00 for 20%
    out_of_network_coinsurance = Column(Numeric(5, 2))
    
    # Prescription drug coverage
    rx_generic_copay = Column(Numeric(10, 2))
    rx_brand_copay = Column(Numeric(10, 2))
    rx_specialty_copay = Column(Numeric(10, 2))
    
    # Additional benefits
    benefits_summary = Column(JSON)  # Structured benefit data from BPS
    exclusions = Column(JSON)        # List of exclusions
    network_info = Column(JSON)      # Network provider information
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    processing_status = Column(String(50), default="pending")  # pending, processing, active, error
    
    # Foreign keys
    tpa_id = Column(String(36), ForeignKey("tpas.id"), nullable=False)
    
    # Relationships
    tpa = relationship("TPA", back_populates="health_plans")
    documents = relationship("Document", back_populates="health_plan", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="health_plan")
    
    def __repr__(self):
        return f"<HealthPlan(name='{self.name}', plan_number='{self.plan_number}')>"