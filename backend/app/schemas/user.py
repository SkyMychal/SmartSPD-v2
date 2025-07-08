"""
User schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    TPA_ADMIN = "tpa_admin"
    CS_MANAGER = "cs_manager"
    CS_AGENT = "cs_agent"
    MEMBER = "member"
    READONLY = "readonly"

class UserBase(BaseModel):
    """Base user schema"""
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None

class UserCreate(UserBase):
    """User creation schema"""
    password: str
    tpa_id: str
    role: UserRole = UserRole.CS_AGENT
    permissions: List[str] = []

class UserUpdate(BaseModel):
    """User update schema"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    role: Optional[UserRole] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None

class UserOut(UserBase):
    """User output schema"""
    id: str
    tpa_id: str
    role: UserRole
    permissions: List[str]
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    login_count: int
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserList(BaseModel):
    """User list response"""
    users: List[UserOut]
    total: int
    page: int
    size: int