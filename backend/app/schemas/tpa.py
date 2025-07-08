"""
TPA schemas
"""
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime

class TPABase(BaseModel):
    """Base TPA schema"""
    name: str
    email: str
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "United States"

class TPACreate(TPABase):
    """TPA creation schema"""
    slug: Optional[str] = None
    subscription_tier: str = "basic"
    max_users: int = 10
    max_health_plans: int = 5
    max_documents: int = 100
    settings: Dict[str, Any] = {}
    branding: Dict[str, Any] = {}
    
    @validator("slug")
    def validate_slug(cls, v):
        if v:
            import re
            if not re.match(r'^[a-z0-9-]+$', v):
                raise ValueError("Slug can only contain lowercase letters, numbers, and hyphens")
        return v

class TPAUpdate(BaseModel):
    """TPA update schema"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None
    subscription_tier: Optional[str] = None
    max_users: Optional[int] = None
    max_health_plans: Optional[int] = None
    max_documents: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None
    branding: Optional[Dict[str, Any]] = None

class TPAOut(TPABase):
    """TPA output schema"""
    id: str
    slug: str
    is_active: bool
    subscription_tier: str
    max_users: int
    max_health_plans: int
    max_documents: int
    settings: Dict[str, Any]
    branding: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TPAStats(BaseModel):
    """TPA statistics"""
    total_users: int
    active_users: int
    total_health_plans: int
    active_health_plans: int
    total_documents: int
    processed_documents: int
    total_conversations: int
    monthly_queries: int