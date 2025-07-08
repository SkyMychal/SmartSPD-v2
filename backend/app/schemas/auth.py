"""
Authentication schemas
"""
from pydantic import BaseModel, field_validator
from typing import Optional
from app.schemas.user import UserOut

class UserLogin(BaseModel):
    """User login request"""
    email: str
    password: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class UserRegister(BaseModel):
    """User registration request"""
    email: str
    password: str
    first_name: str
    last_name: str
    tpa_id: str
    role: str = "cs_agent"
    phone: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional[UserOut] = None

class RefreshToken(BaseModel):
    """Refresh token request"""
    refresh_token: str

class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: str

class PasswordReset(BaseModel):
    """Password reset with token"""
    token: str
    new_password: str
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v