"""
Health Plan schemas
"""
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

class HealthPlanBase(BaseModel):
    """Base health plan schema"""
    name: str
    plan_number: str
    group_id: str  # Required Group ID for TPA identification
    plan_year: int
    effective_date: datetime
    termination_date: Optional[datetime] = None
    plan_type: Optional[str] = None
    description: Optional[str] = None

class HealthPlanCreate(HealthPlanBase):
    """Health plan creation schema"""
    tpa_id: str
    is_active: bool = True
    processing_status: str = "pending"

class HealthPlanUpdate(BaseModel):
    """Health plan update schema"""
    name: Optional[str] = None
    plan_number: Optional[str] = None
    group_id: Optional[str] = None
    plan_year: Optional[int] = None
    effective_date: Optional[datetime] = None
    termination_date: Optional[datetime] = None
    plan_type: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    processing_status: Optional[str] = None
    
    # Coverage amounts
    deductible_individual: Optional[Decimal] = None
    deductible_family: Optional[Decimal] = None
    out_of_pocket_max_individual: Optional[Decimal] = None
    out_of_pocket_max_family: Optional[Decimal] = None
    
    # Copays
    primary_care_copay: Optional[Decimal] = None
    specialist_copay: Optional[Decimal] = None
    urgent_care_copay: Optional[Decimal] = None
    emergency_room_copay: Optional[Decimal] = None
    
    # Coinsurance
    in_network_coinsurance: Optional[Decimal] = None
    out_of_network_coinsurance: Optional[Decimal] = None
    
    # Prescription
    rx_generic_copay: Optional[Decimal] = None
    rx_brand_copay: Optional[Decimal] = None
    rx_specialty_copay: Optional[Decimal] = None
    
    # Additional data
    benefits_summary: Optional[Dict[str, Any]] = None
    exclusions: Optional[Dict[str, Any]] = None
    network_info: Optional[Dict[str, Any]] = None

class HealthPlanOut(HealthPlanBase):
    """Health plan output schema"""
    id: str
    tpa_id: str
    is_active: bool
    processing_status: str
    
    # Coverage amounts
    deductible_individual: Optional[Decimal] = None
    deductible_family: Optional[Decimal] = None
    out_of_pocket_max_individual: Optional[Decimal] = None
    out_of_pocket_max_family: Optional[Decimal] = None
    
    # Copays
    primary_care_copay: Optional[Decimal] = None
    specialist_copay: Optional[Decimal] = None
    urgent_care_copay: Optional[Decimal] = None
    emergency_room_copay: Optional[Decimal] = None
    
    # Coinsurance
    in_network_coinsurance: Optional[Decimal] = None
    out_of_network_coinsurance: Optional[Decimal] = None
    
    # Prescription
    rx_generic_copay: Optional[Decimal] = None
    rx_brand_copay: Optional[Decimal] = None
    rx_specialty_copay: Optional[Decimal] = None
    
    # Additional data
    benefits_summary: Optional[Dict[str, Any]] = None
    exclusions: Optional[Dict[str, Any]] = None
    network_info: Optional[Dict[str, Any]] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class HealthPlanList(BaseModel):
    """Health plan list response"""
    health_plans: List[HealthPlanOut]
    total: int
    page: int
    size: int

class HealthPlanStats(BaseModel):
    """Health plan statistics"""
    total_plans: int
    active_plans: int
    inactive_plans: int
    processing_completed: int